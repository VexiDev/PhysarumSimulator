from collections import Counter

def parse_file(filename):
    x_counter = Counter()
    y_counter = Counter()
    neg_dx_counter = Counter()
    neg_dy_counter = Counter()

    precisionxy = 0  # Change this to the number of decimal places you want to keep

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()

            if line.startswith('#xy'):
                values = line[4:].split(',')
                if len(values) != 2:
                    continue
                try:
                    x, y = map(float, values)
                    x_counter[round(x, precisionxy)] += 1
                    y_counter[round(y, precisionxy)] += 1
                except ValueError:
                    x, y = map(int, values)
                    x_counter[x] += 1
                    y_counter[y] += 1

            elif line.startswith('#dxdy'):
                values = line[6:].split(',')
                if len(values) != 2:
                    continue
                try:
                    dx, dy = map(float, values)
                    if dx < 0:
                        neg_dx_counter[dx] += 1
                    if dy < 0:
                        neg_dy_counter[dy] += 1
                except ValueError:
                    continue

    most_common_x = x_counter.most_common(1)
    most_common_y = y_counter.most_common(1)
    most_common_neg_dx = neg_dx_counter.most_common(1)
    most_common_neg_dy = neg_dy_counter.most_common(1)

    if most_common_x:
        print(f"Most common x coordinate: {most_common_x[0][0]} (Count: {most_common_x[0][1]})")
    else:
        print("No x coordinates found in the file.")

    if most_common_y:
        print(f"Most common y coordinate: {most_common_y[0][0]} (Count: {most_common_y[0][1]})")
    else:
        print("No y coordinates found in the file.")

    if most_common_neg_dx:
        print(f"Most common negative dx value: {most_common_neg_dx[0][0]} (Count: {most_common_neg_dx[0][1]})")
    else:
        print("No negative dx values found in the file.")

    if most_common_neg_dy:
        print(f"Most common negative dy value: {most_common_neg_dy[0][0]} (Count: {most_common_neg_dy[0][1]})")
    else:
        print("No negative dy values found in the file.")

# Usage:
parse_file('output.txt')
