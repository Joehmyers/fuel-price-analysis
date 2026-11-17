"""Stub: Brent crude oil price and sterling exchange rate. Not built; work is paused.

Plan when resumed: fetch the daily Brent price (US dollars a barrel) and the
dollar-to-sterling rate, save each download untouched with its fetch time, and
record when each value became public, as the other fetchers do. Then compare
with the DESNZ weekly pump price to measure the delay before pump prices move.
Pick the sources (and their licences) first and list them in docs/sources.md.
"""


def main() -> None:
    raise NotImplementedError("Brent crude and exchange rate fetching is paused; see docs/sources.md")


if __name__ == "__main__":
    main()
