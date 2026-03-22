try:
    import langchain  # type: ignore

    if not hasattr(langchain, "debug"):
        langchain.debug = False
    if not hasattr(langchain, "verbose"):
        langchain.verbose = False
except Exception:
    pass

