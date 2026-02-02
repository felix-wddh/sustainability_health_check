import streamlit as st
import altair as alt
import pandas as pd

def run_smoke_test():
    try:
        print(f"Streamlit version: {st.__version__}")
        print(f"Altair version: {alt.__version__}")
        print(f"Pandas version: {pd.__version__}")
        
        # Test basic Altair chart creation (this is where the vegalite v4 error often manifests)
        chart = alt.Chart(pd.DataFrame({'x': [1, 2], 'y': [3, 4]})).mark_point().encode(x='x', y='y')
        dict_chart = chart.to_dict()
        
        print("SMOKE_OK", st.__version__, alt.__version__)
    except Exception as e:
        print(f"SMOKE_FAIL: {e}")
        exit(1)

if __name__ == "__main__":
    run_smoke_test()
