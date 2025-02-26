# This script takes the resulting text files from explore_validation.py
# and calculates / displays what percentage of the recipes were
# successfully parsed. The purpose of this is to identify problematic
# websites and reduce the number of parsing errors on the Tamari Explore
# page. Sample output:
# Percent Valid
# therecipecritic.com - 98% (2764/2813)
# minimalistbaker.com - 98% (1654/1689)
# bellyfull.net - 97% (998/1028)

from collections import defaultdict
from urllib.parse import urlparse

def parse_file(file_path):
    domain_counts = defaultdict(int)
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # Extract the domain from the URL
            url = line.split(";")[0]
            domain = urlparse(url).netloc
            domain_counts[domain] += 1
    return domain_counts

def calculate_percentages(valid_counts, invalid_counts):
    results = []
    all_domains = set(valid_counts.keys()).union(invalid_counts.keys())
    
    for domain in all_domains:
        valid = valid_counts.get(domain, 0)
        invalid = invalid_counts.get(domain, 0)
        total = valid + invalid
        percentage = (valid / total) * 100 if total > 0 else 0
        results.append(f"{domain} - {percentage:.0f}% ({valid}/{total})")
    
    return results

def main():
    valid_file = "valid.txt"
    invalid_file = "invalid.txt"
    output_file = "percent-valid.txt"

    # Parse the valid and invalid files
    valid_counts = parse_file(valid_file)
    invalid_counts = parse_file(invalid_file)

    # Calculate percentages
    percentages = calculate_percentages(valid_counts, invalid_counts)

    # Save results to a file
    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write("Percent Valid\n")
        outfile.write("\n".join(percentages) + "\n")

    # Print results
    print("Percent Valid")
    print("\n".join(percentages))

if __name__ == "__main__":
    main()
