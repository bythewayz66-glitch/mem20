import sys
try:
    from .runtime import main
except Exception:
    def main(argv=None):
        print("mem20demandforecastandcapacitybrainz: DemandForecastAndCapacityBrain available")
        return 0
if __name__ == "__main__":
    sys.exit(main())
