try:
    from .mem20enginez.runtime import main
except Exception:
    from mem20enginez.runtime import main
raise SystemExit(main())
