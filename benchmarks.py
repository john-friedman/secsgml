import cProfile
import pstats
from secsgml import parse_sgml_submission_into_memory
from pstats import SortKey
import os

def profile_parser():
    folderpath = 'samples/'
    
    # Create a Profile object
    profiler = cProfile.Profile()
    
    # Profile the function
    profiler.enable()
    for filename in os.listdir(folderpath):
        filepath = os.path.join(folderpath, filename)
        header_metadata, documents = parse_sgml_submission_into_memory(filepath=filepath)
    profiler.disable()
    
    # Print the stats sorted by cumulative time
    stats = pstats.Stats(profiler)
    
    # Print stats for UU decode related functions
    print("\nUU decode related functions (sorted by cumulative time):")
    stats.sort_stats(SortKey.CUMULATIVE).print_stats("decode|binascii|BytesIO")
    
    # Print calls specifically in UU decode
    print("\nDetailed call information for UU decode:")
    stats.print_callers("decode")
    
    # Print specific BytesIO operations in UU decode context
    print("\nByteIO operations:")
    stats.print_callees("decode")

if __name__ == "__main__":
    profile_parser()