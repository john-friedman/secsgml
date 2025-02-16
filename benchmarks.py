import cProfile
import pstats
from secsgml import parse_sgml_submission_into_memory
from pstats import SortKey
import os
import json

def profile_parser():
    folderpath = 'samples/'
    
    # Create a Profile object
    profiler = cProfile.Profile()
    
    # Profile the function
    profiler.enable()
    for filename in os.listdir(folderpath):
        filepath = os.path.join(folderpath, filename)
        header_metadata, documents = parse_sgml_submission_into_memory(filepath=filepath)
        try:
            accn = header_metadata['accession-number']
        except:
            accn = header_metadata['accession number']

        os.makedirs(f'results/{accn}', exist_ok=True)
        for idx,_ in enumerate(header_metadata['documents']):
            try:
                filename = header_metadata['documents'][idx]['filename']
            except:
                filename = header_metadata['documents'][idx]['sequence'] + '.txt'
            with open(f'results/{accn}/{filename}', 'wb') as f:
                f.write(documents[idx])

        # write the header metadata to a file in results folder as json
        with open(f'results/{accn}/header_metadata.json', 'w') as f:
            json.dump(header_metadata, f, indent=4)


    profiler.disable()
    
    # Print the stats sorted by cumulative time
    stats = pstats.Stats(profiler)
    
    # Print top 20 time-consuming functions
    print("\nTop 20 time-consuming functions (sorted by cumulative time):")
    stats.sort_stats(SortKey.CUMULATIVE).print_stats(20)
    
    # Print top 20 functions by number of calls
    print("\nTop 20 functions by number of calls:")
    stats.sort_stats(SortKey.CALLS).print_stats(20)
    
    # Print detailed stats for functions containing 'parse' in their name
    print("\nDetailed stats for parsing-related functions:")
    stats.sort_stats(SortKey.CUMULATIVE).print_stats("parse")


if __name__ == "__main__":
    os.makedirs('results', exist_ok=True)
    profile_parser()