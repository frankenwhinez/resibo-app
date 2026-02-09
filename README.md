# 💰 Resibo - Multilingual Expense Tracker

A chat-based expense tracker that supports **English**, **Tagalog**, and **Bisaya (Cebuano)**.

## Features

✅ **Natural Language Processing** - Just type your expenses naturally  
✅ **Multilingual Support** - English, Tagalog, and Bisaya  
✅ **10 Smart Categories** - Auto-categorizes your expenses intelligently  
✅ **Custom Categories** - Add your own categories with custom keywords  
✅ **Manual Override** - Change category before saving if auto-detection is wrong  
✅ **Real-time Totals** - Running total of all expenses  
✅ **Category Breakdown** - See spending by category with percentages  
✅ **Export to CSV** - Download your expense history  
✅ **Chat Interface** - Conversational expense logging  

## Installation

1. **Install Python** (3.8 or higher)

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the app:**
   ```bash
   streamlit run resibo_app.py
   ```

2. **Start logging expenses** by typing naturally in the chat:

   **English Examples:**
   - "I spent 50 for coffee"
   - "Bought lunch for 85 pesos"
   - "Paid 200 for groceries"

   **Tagalog Examples:**
   - "Bumili ako ng bigas sa halagang 200"
   - "Nagbayad ako ng 50 para sa load"
   - "Gastos ko sa jeep 15 pesos"

   **Bisaya Examples:**
   - "Plete nako sa jeep kay 15 pesos"
   - "Gipalit nako nga pagkaon 100"
   - "Gibayad nako 50 sa load"

## How It Works

For each expense entry, Resibo:

1. **Detects Language** - Identifies if you're speaking English, Tagalog, or Bisaya
2. **Extracts Data** - Pulls out the amount, item, and auto-assigns category
3. **Shows Summary** - Displays a structured summary in a table
4. **Asks Confirmation** - Confirms before saving to your Daily Log
5. **Updates Total** - Shows running total and category breakdown

## Categories

Resibo comes with **10 smart default categories**:

1. 🍔 **Food & Dining** - Meals, snacks, groceries, restaurants
2. 🚌 **Transport** - Jeep, taxi, gas, parking, Grab
3. 💡 **Bills & Utilities** - Electric, water, internet, phone bills
4. 🛍️ **Shopping** - Clothes, gadgets, personal items
5. 💊 **Health & Wellness** - Medicine, doctor, gym, vitamins
6. 💇 **Personal Care** - Haircut, salon, cosmetics, grooming
7. 🎬 **Entertainment** - Movies, games, Netflix, hobbies
8. 📚 **Education** - Tuition, books, courses, school supplies
9. 🎁 **Gifts & Others** - Presents, donations, church offerings
10. 📦 **Miscellaneous** - Everything else

### Custom Categories

You can add your own categories! Examples:
- **Pets** - Dog food, vet, pet supplies
- **Subscriptions** - Netflix, Spotify, gym membership
- **Insurance** - Health, car, life insurance
- **Debt Payments** - Credit card, loans

## Tips

- 🌐 You can mix languages! The app detects each message individually
- ❓ If amount or item is missing, the app will ask you to clarify
- 📂 **Change the category** before saving using the dropdown
- ➕ **Add custom categories** in the sidebar for personalized tracking
- 📊 View percentages per category in the sidebar breakdown
- 📥 **Export your data** to CSV anytime from the sidebar
- 🗑️ Clear all expenses anytime with the "Clear All" button

## License

Free to use and modify!
