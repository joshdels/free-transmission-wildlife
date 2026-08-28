"""This is for testing the query if it loads"""

from load_data import load_data

from queries import (
    summarize_transmission_lines,
    summarize_wildlife_lands,
    find_wildlife_hit_by_transmission,
    calculate_overlap_km,
)

con = load_data()


print(summarize_transmission_lines(con))
print(summarize_wildlife_lands(con))
print(find_wildlife_hit_by_transmission(con))
print(calculate_overlap_km(con))
