from load_data import load_data

from queries import (
    summarize_transmission_lines,
    find_wildlife_hit_by_transmission,
    calculate_overlap_km,
)

con = load_data()



print(summarize_transmission_lines(con))
print(find_wildlife_hit_by_transmission(con))
print(calculate_overlap_km(con))
