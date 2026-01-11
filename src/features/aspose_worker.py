import sys
import os

# Set console output encoding to UTF-8 to handle special characters correctly
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# Mock audit_logger to avoid import issues or dependency on the main app structure
# inside this isolated worker
class MockLogger:
    def log_event(self, *args, **kwargs):
        pass

# Add the parent directory to sys.path to ensure we can import typical modules if needed
# though for this isolated script we try to keep dependencies minimal
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def convert(input_path, output_path):
    try:
        import aspose.slides as slides
    except ImportError:
        print("Error: Aspose.Slides is not installed.", file=sys.stderr)
        sys.exit(2) # Code 2: Not installed

    try:
        if not os.path.exists(input_path):
             print(f"Error: Input file not found: {input_path}", file=sys.stderr)
             sys.exit(3)

        with slides.Presentation() as pres:
            # Aspose.Slides creates a default presentation with one empty slide.
            # We remove it so we only have the PDF slides.
            pres.slides.remove_at(0)
            
            # Using add_from_pdf method
            pres.slides.add_from_pdf(input_path)
            
            # Save the result
            pres.save(output_path, slides.export.SaveFormat.PPTX)
            
        print("Success: Conversion completed.")
        sys.exit(0) # Code 0: Success

    except Exception as e:
        # Print the exception to stderr so the calling process can capture it
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1) # Code 1: Runtime Error

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python aspose_worker.py <input_pdf> <output_pptx>", file=sys.stderr)
        sys.exit(4) # Code 4: Invalid arguments
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    convert(input_file, output_file)
