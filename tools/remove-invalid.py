# This file is used to construct the Explore text files for Version 1.1

# invalid.txt contains lines that did not pass explore_validation.py
# websites-to-remove-invalid.txt contains a list of websites that I
# intend to remove invalid lines (excludes taste.com.au that bans IPs)

# For every line in explore-all-randomized-v1.0.txt:
# If 1) line in invalid.txt AND 2) line contains string from
# websites-to-remove-invalid.txt,
# The line is not included in Version 1.1 text file

def main():
    # 1) Read invalid lines into a set
    invalid_lines = set()
    with open("invalid.txt", "r", encoding="utf-8") as f_invalid:
        for line in f_invalid:
            invalid_lines.add(line.rstrip("\n"))

    # 2) Read domains to remove into a list
    websites_to_remove = []
    with open("websites-to-remove-invalid.txt", "r", encoding="utf-8") as f_web:
        for domain in f_web:
            websites_to_remove.append(domain.strip())

    # 3) Process explore-all-randomized-v1.0.txt and write to explore-all-randomized.txt
    with open("explore-all-randomized-v1.0.txt", "r", encoding="utf-8") as f_in, \
         open("explore-all-randomized.txt", "w", encoding="utf-8") as f_out:

        for line in f_in:
            stripped_line = line.rstrip("\n")

            # Check if line is in invalid AND contains a domain from websites_to_remove
            in_invalid = stripped_line in invalid_lines
            contains_domain = any(domain in stripped_line for domain in websites_to_remove)

            # Exclude only if BOTH conditions are True
            if not (in_invalid and contains_domain):
                f_out.write(line)

if __name__ == "__main__":
    main()
