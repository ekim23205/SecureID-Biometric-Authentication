import statistics

# SecureID - Facial Authentication Reliability Testing
# No facial images or biometric templates are stored.

MATCH_THRESHOLD = 60


def collect_distances():
    print("\nSecureID Authentication Testing")
    print("Enter distances from your own verification tests.")
    print("Press Enter on a blank line to finish.\n")

    distances = []

    while True:
        value = input("Verification distance: ").strip()

        if not value:
            break

        try:
            distance = float(value)

            if not 0 <= distance <= 1000:
                print("Enter a reasonable nonnegative distance.")
                continue

            distances.append(distance)

        except ValueError:
            print("Please enter a valid number.")

    return distances


def analyze_results(distances):
    if not distances:
        print("No results provided.")
        return

    matches = sum(
        distance < MATCH_THRESHOLD
        for distance in distances
    )

    failures = len(distances) - matches

    print("\n--- SecureID Test Report ---")
    print("Total attempts:", len(distances))
    print("Demo matches:", matches)
    print("Rejected attempts:", failures)
    print(
        "Average distance:",
        round(statistics.mean(distances), 2)
    )
    print(
        "Lowest distance:",
        round(min(distances), 2)
    )
    print(
        "Highest distance:",
        round(max(distances), 2)
    )

    match_rate = matches / len(distances) * 100

    print("Demo match rate:", round(match_rate, 1), "%")
    print("Experimental threshold:", MATCH_THRESHOLD)

    print("\nThis is not a validated biometric")
    print("security or anti-spoofing evaluation.")


if __name__ == "__main__":
    results = collect_distances()
    analyze_results(results)
