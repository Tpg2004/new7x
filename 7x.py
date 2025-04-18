import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Set up page
st.set_page_config(page_title="Nomora AI", layout="wide", page_icon="🍽️")

# Centered Logo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://raw.githubusercontent.com/Tpg2004/nomora-ai/main/assets/nomoraig.jpeg", width=150)

st.title("Nomora AI")
st.markdown("#### 🍄 Smart Menu Insights to Reduce Food Waste & Boost Efficiency")
st.markdown("---")

# Load CSVs safely
@st.cache_data
def load_data():
    dishes = pd.read_csv("data/dish_sales.csv")
    waste = pd.read_csv("data/ingredient_waste.csv")
    return dishes, waste

dishes_df, waste_df = load_data()

# Dish Performance Section
st.subheader("📉 Low-Performing Dishes")
low_performers = dishes_df[dishes_df['Weekly Orders'] < 30].sort_values(by='Weekly Orders')
st.write("These dishes had low orders. Consider removing or reworking them:")
st.dataframe(low_performers[['Dish Name', 'Weekly Orders', 'Profit Margin', 'Ingredient Cost']])

# Waste Section
st.subheader("🗑️ High-Waste Ingredients")
high_waste = waste_df.sort_values(by='waste_kg', ascending=False).head(5)
chart = alt.Chart(high_waste).mark_bar().encode(
    x=alt.X('ingredient', sort='-y'),
    y='waste_kg',
    color=alt.value('orange')
).properties(width=600, height=300)
st.altair_chart(chart)
st.write("Top wasted ingredients to focus on repurposing or reducing.")

# Suggested Recipes
st.subheader("🍽️ Suggested New Dishes Using Wasted Ingredients")
suggested_dishes = {
    "Creamy Mushroom Soup": ["Mushrooms", "Cream", "Onion"],
    "Stuffed Bell Peppers": ["Bell Peppers", "Rice", "Cheese"],
    "Veggie Frittata": ["Spinach", "Eggs", "Cheese"]
}
for dish, ingredients in suggested_dishes.items():
    st.markdown(f"**{dish}** – Uses: _{', '.join(ingredients)}_")

# Ingredient Overlap
st.subheader("🔁 High-Margin Dishes with Ingredient Overlap")
common_ingredients = dishes_df['Ingredients'].str.split(', ').explode().value_counts().reset_index()
common_ingredients.columns = ['Ingredient', 'Dish Count']
st.dataframe(common_ingredients.head(10))

# Load Mini LLM Model
@st.cache_resource
def load_local_llm():
    tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
    model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")
    return tokenizer, model

tokenizer, model = load_local_llm()

def ask_nomora_ai(query):
    input_text = f"Restaurant assistant: {query}"
    inputs = tokenizer(input_text, return_tensors="pt", max_length=128, truncation=True)
    outputs = model.generate(**inputs, max_new_tokens=100)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

# Chatbot
st.markdown("## 🤖 Ask Nomora AI")
user_query = st.chat_input("Ask a question about your menu or waste...")

if user_query:
    user_query = user_query.lower()

    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        response = ""

        if user_query in ["hi", "hello", "hey"]:
            response = "👋 Hey there! Nomora is so delighted to meet you!"

        elif "most wasted" in user_query or "high waste" in user_query:
            top_waste = waste_df.sort_values(by='waste_kg', ascending=False).iloc[0]
            response = f"🔝 The most wasted ingredient is **{top_waste['ingredient']}**, with **{top_waste['waste_kg']} kg** wasted."

        elif "remove" in user_query or "low orders" in user_query:
            low_dish = dishes_df.sort_values(by='Weekly Orders').iloc[0]
            response = f"⚠️ Consider removing **{low_dish['Dish Name']}** – it had just **{low_dish['Weekly Orders']}** orders last week."

        elif "suggest" in user_query or "new dish" in user_query:
            response = "👩‍🍳 Try creating new dishes using high-waste ingredients like Avocado or Lemon. For example:\n\n- **Avocado Hummus Wrap**\n- **Lemon Herb Pasta**"

        elif "overlap" in user_query or "common ingredient" in user_query:
            common = dishes_df['Ingredients'].str.split(', ').explode().value_counts().head(1)
            ingredient = common.index[0]
            response = f"🔁 The most common ingredient across dishes is **{ingredient}**. Use it wisely to reduce waste."

        elif "profit" in user_query:
            for _, row in dishes_df.iterrows():
                if row['Dish Name'].lower() in user_query:
                    response = f"💰 The profit margin of **{row['Dish Name']}** is **{row['Profit Margin']}**."
                    break
            else:
                response = "I couldn't find that dish. Please check the name and try again."

        elif "shelf life" in user_query:
            for _, row in waste_df.iterrows():
                if row['ingredient'].lower() in user_query:
                    response = f"🧊 The shelf life of **{row['ingredient']}** is **{row['shelf_life']}**."
                    break
            else:
                response = "I couldn't find shelf life info for that ingredient."

        else:
            response = ask_nomora_ai(user_query)

        st.write(response)

# Footer
st.markdown("---")
st.markdown("💡 **Nomora AI** empowers restaurants to cut costs, reduce waste, and reimagine menus with data.")
