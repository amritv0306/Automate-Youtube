import os
from google import genai
import time

def generate_image_from_description(description, api_key, output_path="generated_images"):
    """Generate an image using Google's Imagen 3 model based on a text description."""
    # Configure the Gemini API client
    client = genai.Client(api_key=api_key)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    print(f"Generating image for: {description}")
    
    # Generate the image
    response = client.models.generate_images(
        model="imagen-3.0-generate-002",
        prompt=description,
        config={
            "aspect_ratio": "9:16",  # Setting 9:16 ratio as requested
            "number_of_images": 1
        }
    )
    
    # Save the generated image
    if response.generated_images:
        # Create a filename based on a simplified version of the description
        safe_description = "".join(c for c in description[:30] if c.isalnum() or c.isspace()).strip()
        safe_description = safe_description.replace(" ", "_")
        filename = f"{safe_description}.png"
        filepath = os.path.join(output_path, filename)
        
        # Save the image
        with open(filepath, "wb") as f:
            f.write(response.generated_images[0].image.data)
        
        print(f"Image saved to: {filepath}")
        return filepath
    else:
        print("No images were generated.")
        return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate AI images from text descriptions using Google's Imagen 3")
    parser.add_argument("description", help="Description of the image to generate")
    parser.add_argument("--api-key", required=True, help="Google Gemini API key")
    parser.add_argument("--output", default="generated_images", help="Output directory for generated images")
    args = parser.parse_args()
    
    # Generate the image
    generated_image = generate_image_from_description(
        args.description, 
        args.api_key,
        args.output
    )
    
    if generated_image:
        print("\nImage generation completed successfully!")
    else:
        print("\nNo images were generated. Please check your API key and try again.")

if __name__ == "__main__":
    main()
