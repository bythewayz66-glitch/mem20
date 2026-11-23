import sys
try:
    from .runtime import main
except Exception:
    def main(argv=None):
        from .domain import FaultContainmentCells, estate_context
        print("mem20faultcontainmentcellsz: FaultContainmentCells available")
        return 0
if __name__ == "__main__":
    sys.exit(main())
