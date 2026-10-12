import repositories.factory_a as fa, repositories.factory_b as fb
fa.USE_SUPABASE_USERS=False
for k in ("USE_SUPABASE_LISTINGS","USE_SUPABASE_TRANSACTIONS","USE_SUPABASE_REVIEWS"): setattr(fb,k,False)
import streamlit as st
st.set_page_config(layout="wide")
exec(open("views/pages/login_and_register.py").read())
