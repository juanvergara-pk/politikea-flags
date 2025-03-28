import os
import cv2
import numpy as np

# Run without matplotlib when deployed in the cloud
CLOUD_DEPLOYMENT = os.getenv("CLOUD_DEPLOYMENT")
if not CLOUD_DEPLOYMENT:
    import matplotlib.pyplot as plt

def detect_borders(image, min_line_length=100, iterations=2, kernel_len=30, edge_perc=0.3,
                           debug = False):
    """
    Detect vertical and horizontal lines in an image, merging broken lines using morphological operations.

    Args:
        image_data (img): Input image in cv2 format.
        min_line_length (int): Minimum length of lines to be considered.

    Returns:
        None
    """
    # Step 1: Read the image
    #image_data = cv2.imread(image_path)
    if image is None:
        print("Error: Unable to read the image at the specified path.")
        return
    height, width, color_depth = image.shape

    # Step 2: Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 3: Apply Canny Edge Detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=7) #3) #5)

    # Step 4: Define kernels for vertical and horizontal line detection
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))  # Tall, narrow kernel
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))  # Wide, short kernel

    # Step 5: Detect vertical and horizontal lines
    vertical_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel, iterations=iterations)
    horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel, iterations=iterations)

    # Step 6: Merge broken lines using dilation and closing
    merged_vertical = cv2.morphologyEx(vertical_lines, cv2.MORPH_CLOSE, vertical_kernel, iterations=4)
    merged_horizontal = cv2.morphologyEx(horizontal_lines, cv2.MORPH_CLOSE, horizontal_kernel, iterations=4)

    # Combine the vertical and horizontal lines
    combined_lines = cv2.addWeighted(merged_vertical, 1.0, merged_horizontal, 1.0, 0.0)

    # Step 7: Filter out small line segments (one image at a time)
    filtered_lines_v = np.zeros_like(merged_vertical)
    filtered_lines_h = np.zeros_like(merged_horizontal)
    for img, filtered_lines in zip([merged_vertical, merged_horizontal], [filtered_lines_v, filtered_lines_h]):
        contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if max(w, h) >= min_line_length:
                cv2.drawContours(filtered_lines, [contour], -1, 255, thickness=cv2.FILLED)

    # Combine the vertical and horizontal lines
    filtered_lines = cv2.addWeighted(filtered_lines_v, 1.0, filtered_lines_h, 1.0, 0.0)

    # Step 8: Add filtered lines to the original image
    # - Emphasize the lines with dilations, and add them in red
    dilation_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    filtered_enlarged = cv2.dilate(filtered_lines.copy(), dilation_kernel, iterations=2)
    output_image = gray.copy()
    output_image = cv2.cvtColor(output_image, cv2.COLOR_GRAY2RGB) #cv2.COLOR_GRAY2BGR)
    output_image[filtered_enlarged == 255] = [255, 0, 0]  # Red color for lines

    if debug and not CLOUD_DEPLOYMENT:
        # Debug Step: Visualize the results using matplotlib
        fig, axes = plt.subplots(3, 4, figsize=(20, 10))
        axes = axes.ravel()

        images = [
            ("Original Image", cv2.cvtColor(image, cv2.COLOR_BGR2RGB)),
            ("Edges (Canny)", edges),
            ("Vertical Lines (Raw)", vertical_lines),
            ("Horizontal Lines (Raw)", horizontal_lines),
            ("Merged Vertical Lines", merged_vertical),
            ("Merged Horizontal Lines", merged_horizontal),
            ("Combined Lines", combined_lines),
            ("Filtered Lines", filtered_lines),
            ("Output Lines", output_image),
        ]

        for i, (title, img) in enumerate(images):
            if len(img.shape) == 2:  # Grayscale image
                axes[i].imshow(img, cmap='gray')
            else:  # RGB image
                axes[i].imshow(img)
            axes[i].set_title(title)
            axes[i].axis('off')

        plt.tight_layout()
        plt.show()


    # Step 9: Count pixels near the edges
    _, _, top_sum, bottom_sum = _count_border_pixels(filtered_lines_h, edge_width=int(height*edge_perc))
    horizontal_line_sum = top_sum + bottom_sum
    left_sum, right_sum, _, _ = _count_border_pixels(filtered_lines_v, edge_width=int(width*edge_perc))
    vertical_line_sum = left_sum + right_sum

    # Step 9.1: Create a classification based on the border sums
    # Algo Params: Border Detection.
    high_score = 5000
    middle_score = 1000
    low_score = 100
    # Algo Params: Pixel Deviation Along Edges.
    narrow_edge_perc = 0.07
    threshold = 10.0
    image_has_border = False
    # Score based on the border sums first, and then check the pixel deviation along the edges.
    if horizontal_line_sum > high_score:
        if vertical_line_sum > low_score:
            #image_has_border = True
            _, _, top_dev, bottom_dev = _get_px_dev_per_edge(image, edge_perc=narrow_edge_perc)
            print(f"Top Dev: {top_dev}, Bottom Dev: {bottom_dev}")
            if top_dev < threshold and bottom_dev < threshold:
                image_has_border = True
    if vertical_line_sum > high_score:
        if horizontal_line_sum > low_score:
            #image_has_border = True
            left_dev, right_dev, _, _ = _get_px_dev_per_edge(image, edge_perc=narrow_edge_perc)
            print(f"Left Dev: {left_dev}, Right Dev: {right_dev}")
            if left_dev < threshold and right_dev < threshold:
                image_has_border = True
    if horizontal_line_sum > middle_score and vertical_line_sum > middle_score:
        #image_has_border = True
        left_dev, right_dev, top_dev, bottom_dev = _get_px_dev_per_edge(image, edge_perc=narrow_edge_perc)
        print(f"Left Dev: {left_dev}, Right Dev: {right_dev}, Top Dev: {top_dev}, Bottom Dev: {bottom_dev}")
        if (left_dev < threshold and right_dev < threshold) or (top_dev < threshold and bottom_dev < threshold):
            image_has_border = True
    
    # Step 10: Return the line sums for borders
    if debug:
        print(f"Horizontal Line Sum (Edges): {horizontal_line_sum}")
        print(f"Vertical Line Sum (Edges): {vertical_line_sum}")
    
    return image_has_border, (horizontal_line_sum, vertical_line_sum), output_image


def _count_border_pixels(img, edge_width=500):
    """
    Count white pixels in the border regions of an image.
    Args:
        img (np.array): Filtered binary image.
        edge_width (int): Width of the border region to consider.

    Returns:
        int: Sum of white pixels in the border region.
    """
    height, width = img.shape
    # Top and bottom edges for horizontal lines
    top_edge = img[:edge_width, :]
    bottom_edge = img[-edge_width:, :]
    # Left and right edges for vertical lines
    left_edge = img[:, :edge_width]
    right_edge = img[:, -edge_width:]
    # Sum white pixels in each region
    return (
        np.sum(left_edge == 255),
        np.sum(right_edge == 255),
        np.sum(top_edge == 255),
        np.sum(bottom_edge == 255),
    )


def _get_px_dev_per_edge(image, edge_perc=0.07, debug=False):

    # Read the image size
    height, width, color_depth = image.shape

    # Convert to grayscale if necessary
    if color_depth == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif color_depth == 1:
        gray = image
    else:
        raise ValueError("Invalid image color depth. Must be 1 or 3.")

    # Apply Gaussian Blur to reduce noise
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Calculate the standard deviation of pixel values along the edges
    edge_width = int(width * edge_perc)
    edge_height = int(height * edge_perc)


    # Check the standard deviation of pixel values along the edges

    # CHECK TOP EDGE. FLATTEN. CALCULATE STD DEV
    top_edge = gray[:edge_height, :]
    top_edge = top_edge.reshape(edge_height * width)
    top_edge_dev = np.std(top_edge)

    # CHECK BOTTOM EDGE. FLATTEN. CALCULATE STD DEV
    bottom_edge = gray[(height-edge_height):, :]
    bottom_edge = bottom_edge.reshape(edge_height * width)
    bottom_edge_dev = np.std(bottom_edge)

    # CHECK LEFT EDGE. FLATTEN. CALCULATE STD DEV
    left_edge = gray[:, :edge_width]
    left_edge = left_edge.reshape(height * edge_width)
    left_edge_dev = np.std(left_edge)

    # CHECK RIGHT EDGE. FLATTEN. CALCULATE STD DEV
    right_edge = gray[:, (width-edge_width):]
    right_edge = right_edge.reshape(height * edge_width)
    right_edge_dev = np.std(right_edge)

    return (
        left_edge_dev,
        right_edge_dev,
        top_edge_dev,
        bottom_edge_dev
    )

