import streamlit as st
import pandas as pd
from datetime import datetime

# Load and preprocess data
def load_data():
    ingredients_df = pd.read_csv("ingredient_waste.csv")
    dishes_df = pd.read_csv("dish_sales.csv")
    
    # Clean and transform dish data
    dishes_df['Ingredients'] = dishes_df['Ingredients'].str.split(", ")
    
    # Extract numerical values from currency columns
    dishes_df['Ingredient Cost'] = dishes_df['Ingredient Cost'].str.extract(r'₹(\d+)').astype(int)
    dishes_df['Profit Margin'] = dishes_df['Profit Margin'].str.extract(r'₹(\d+)').astype(int)
    
    # Parse waste percentages
    dishes_df['Primary Waste Ingredient'] = dishes_df['Ingredient Waste'].str.split(" - ").str[0]
    dishes_df['Waste Percentage'] = dishes_df['Ingredient Waste'].str.split(" - ").str[1].str.replace("%", "").astype(float)
    
    return dishes_df, ingredients_df

dishes_df, ingredients_df = load_data()

# Nomora AI Engine
class NomoraAI:
    def get_low_performers(self, df):
        return df[(df['Weekly Orders'] < 10) & (df['Waste Percentage'] > 20)]

    def get_high_waste_ingredients(self, df):
        return df.sort_values('Avg Waste %', ascending=False).head(3)

    def get_high_margin_overlap(self, df):
        df['Overlap Score'] = df['Ingredients'].apply(lambda x: len(set(x)))
        return df.sort_values(['Profit Margin', 'Overlap Score'], ascending=[False, False])

    def suggest_new_dishes(self, waste_df):
        suggestions = waste_df.set_index('Ingredient')['Suggested Action'].to_dict()
        return {ing: [s.strip() for s in sug.split("; ")] for ing, sug in suggestions.items()}

# Chatbot Logic
def handle_query(query, ai, dishes_df, ingredients_df):
    response = {"title": "", "content": "", "visual": None}
    
    if 'remove' in query:
        low_performers = ai.get_low_performers(dishes_df)
        response["title"] = "Dishes to Consider Removing/Repurposing"
        response["content"] = low_performers[['Dish Name', 'Weekly Orders', 'Primary Waste Ingredient', 'Waste Percentage']]
        
    elif 'wasted' in query:
        top_waste = ai.get_high_waste_ingredients(ingredients_df)
        response["title"] = "Most Wasted Ingredients"
        response["content"] = top_waste[['Ingredient', 'Avg Waste %', 'Frequently Wasted In']]
        
    elif 'new dishes' in query:
        suggestions = ai.suggest_new_dishes(ingredients_df)
        content = "\n\n".join([f"**{k}**:\n- " + "\n- ".join(v) for k,v in suggestions.items()])
        response["title"] = "Suggested Waste Reduction Actions"
        response["content"] = content
        
    elif 'overlapping' in query:
        overlap = ai.get_high_margin_overlap(dishes_df)
        response["title"] = "High Margin Dishes with Ingredient Overlap"
        response["content"] = overlap[['Dish Name', 'Profit Margin', 'Ingredients']]
        
    else:
        response["content"] = "I'm sorry, I didn't understand that question. Please try rephrasing."
    
    return response

# UI Setup
st.set_page_config(page_title="Nomora AI", page_icon="🍽️", layout="wide")

with st.sidebar:
    st.header("Settings")
    start_date = st.date_input("Analysis Period Start", datetime.today())
    end_date = st.date_input("Analysis Period End", datetime.today())
    st.divider()
    st.caption("Powered by Nomora AI • v1.0")

st.title("🍽️ Nomora AI - Smart Restaurant Assistant")
st.write("Reduce food waste and maximize profits through AI-driven insights")

# Dashboard Section
tab1, tab2 = st.tabs(["📊 Waste Analytics", "💬 AI Assistant"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Weekly Orders", dishes_df['Weekly Orders'].sum())
    with col2:
        top_waste = ingredients_df.nlargest(1, 'Avg Waste %')
        st.metric("Highest Waste Ingredient", 
                 f"{top_waste['Ingredient'].values[0]} ({top_waste['Avg Waste %'].values[0]}%)")
    with col3:
        low_performers = NomoraAI().get_low_performers(dishes_df)
        st.metric("Dishes Needing Attention", len(low_performers))
    
    st.divider()
    
    col4, col5 = st.columns(2)
    with col4:
        st.subheader("Ingredient Waste Breakdown")
        st.bar_chart(ingredients_df.set_index('Ingredient')['Avg Waste %'])
    
    with col5:
        st.subheader("Dish Performance")
        st.write("Weekly Orders vs Waste Percentage")
        st.line_chart(dishes_df.set_index('Dish Name')[['Weekly Orders', 'Waste Percentage']])

with tab2:
    st.subheader("Nomora AI Chat")
    query = st.text_input("Ask a question about your menu...", key="chat_input")
    
    if query:
        ai = NomoraAI()
        response = handle_query(query.lower(), ai, dishes_df, ingredients_df)
        
        with st.chat_message("assistant"):
            if response["title"]:
                st.subheader(response["title"])
            
            if isinstance(response["content"], pd.DataFrame):
                st.dataframe(response["content"], hide_index=True)
            elif isinstance(response["content"], str):
                st.markdown(response["content"])
                
        st.button("Ask Another Question", use_container_width=True)
