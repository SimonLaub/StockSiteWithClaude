from model import train_ticker
from stocks import STOCKS


def main():
    for ticker in STOCKS:
        print(f"Training {ticker}...")
        train_ticker(ticker)


if __name__ == "__main__":
    main()
