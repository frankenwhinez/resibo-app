import streamlit as st
import pandas as pd
from datetime import datetime
import re

# Page configuration
st.set_page_config(
    page_title="Resibo - Expense Tracker",
    page_icon="💰",
    layout="centered"
)

# Initialize session state
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
if 'pending_expense' not in st.session_state:
    st.session_state.pending_expense = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'custom_categories' not in st.session_state:
    st.session_state.custom_categories = {}  # Store custom categories: {name: [keywords]}

# Language detection keywords
LANGUAGE_PATTERNS = {
    'tagalog': ['bumili', 'binili', 'binayad', 'bayad', 'gastos', 'gumastos', 'nagbayad'],
    'bisaya': ['plete', 'palit', 'gipalit', 'gibayad', 'bayad', 'gasto']
}

# Category keywords for auto-classification (ordered by priority for better matching)
CATEGORY_KEYWORDS = {
    'Food & Dining': [
        # General food
        'food', 'meal', 'lunch', 'dinner', 'breakfast', 'snack', 'merienda',
        # Filipino foods
        'rice', 'bigas', 'ulam', 'kaon', 'pagkaon', 'sud-an',
        # Dining
        'restaurant', 'jollibee', 'mcdo', 'mcdonald', 'kfc', 'pizza', 'burger',
        'coffee', 'kape', 'starbucks', 'cafe', 'carinderia', 'turo-turo',
        # Groceries
        'grocery', 'groceries', 'palengke', 'market', 'supermarket', 'sari-sari',
        'vegetables', 'gulay', 'meat', 'karne', 'fish', 'isda', 'fruits', 'prutas'
    ],
    'Transport': [
        'transport', 'fare', 'plete', 'pamasahe', 
        'jeep', 'jeepney', 'tricycle', 'trike', 'habal-habal', 'motor',
        'bus', 'taxi', 'grab', 'angkas', 'uber', 'sakay',
        'gas', 'gasolina', 'diesel', 'fuel', 'parking'
    ],
    'Bills & Utilities': [
        'bill', 'bills', 'bayad', 'utilities',
        'electric', 'electricity', 'kuryente', 'meralco',
        'water', 'tubig', 'maynilad',
        'internet', 'wifi', 'pldt', 'globe', 'smart',
        'phone', 'mobile', 'postpaid', 'plan'
    ],
    'Shopping': [
        'shopping', 'shop', 'clothes', 'clothing', 'damit',
        'shirt', 'pants', 'shoes', 'sapatos', 'sandals', 'tsinelas',
        'bag', 'wallet', 'watch', 'accessories',
        'gadget', 'phone', 'cellphone', 'laptop', 'earphones', 'charger'
    ],
    'Health & Wellness': [
        'health', 'medicine', 'gamot', 'bulong', 'tambal',
        'doctor', 'doktor', 'hospital', 'clinic', 'checkup',
        'vitamins', 'supplement', 'pharmacy', 'botika', 'mercury',
        'gym', 'fitness', 'workout', 'yoga', 'massage', 'hilot'
    ],
    'Personal Care': [
        'haircut', 'gupit', 'salon', 'barber', 'parlor',
        'shampoo', 'soap', 'sabon', 'toothpaste', 'deodorant',
        'cosmetics', 'makeup', 'skincare', 'lotion', 'perfume', 'pabango',
        'grooming', 'beauty', 'nails', 'spa'
    ],
    'Entertainment': [
        'entertainment', 'movie', 'cinema', 'netflix', 'spotify',
        'concert', 'gig', 'show', 'theater',
        'games', 'gaming', 'ps5', 'xbox', 'nintendo', 'mobile legends', 'ml',
        'hobby', 'books', 'libro', 'magazine', 'comics'
    ],
    'Education': [
        'education', 'school', 'eskwela', 'tuition', 'enrollment',
        'books', 'libro', 'notebook', 'pen', 'ballpen', 'school supplies',
        'course', 'training', 'seminar', 'workshop', 'online class',
        'photocopies', 'xerox', 'print', 'printing'
    ],
    'Gifts & Others': [
        'gift', 'regalo', 'birthday', 'kaarawan',
        'donation', 'donasyon', 'charity', 'church', 'simbahan',
        'offering', 'abuloy', 'contribution'
    ],
    'Miscellaneous': []
}

def detect_language(text):
    """Detect if text is in English, Tagalog, or Bisaya"""
    text_lower = text.lower()
    
    for word in LANGUAGE_PATTERNS['tagalog']:
        if word in text_lower:
            return 'tagalog'
    
    for word in LANGUAGE_PATTERNS['bisaya']:
        if word in text_lower:
            return 'bisaya'
    
    return 'english'

def extract_amount(text):
    """Extract numerical amount from text"""
    # Look for patterns like "50", "50 pesos", "₱50", "php 50"
    patterns = [
        r'₱\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*(?:pesos?|php)',
        r'\b(\d+(?:\.\d+)?)\b'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return float(match.group(1))
    
    return None

def extract_item(text, amount):
    """Extract item/service from text"""
    # Remove amount-related words
    cleaned = re.sub(r'₱?\d+(?:\.\d+)?\s*(?:pesos?|php)?', '', text, flags=re.IGNORECASE)
    
    # Remove common transaction words
    remove_words = ['bumili', 'binili', 'bought', 'paid', 'for', 'ako', 'ng', 'sa', 'nako', 'ko', 
                    'gipalit', 'gibayad', 'spent', 'halagang', 'kay', 'og']
    
    for word in remove_words:
        cleaned = re.sub(r'\b' + word + r'\b', '', cleaned, flags=re.IGNORECASE)
    
    # Clean up whitespace
    cleaned = ' '.join(cleaned.split()).strip()
    
    return cleaned if cleaned else None

def categorize_item(item_text):
    """Auto-assign category based on item keywords with priority matching"""
    if not item_text:
        return 'Miscellaneous'
    
    item_lower = item_text.lower()
    
    # First check custom categories (higher priority)
    for category, keywords in st.session_state.custom_categories.items():
        for keyword in keywords:
            if keyword.lower() in item_lower:
                return category
    
    # Then check default categories
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == 'Miscellaneous':
            continue
        for keyword in keywords:
            if keyword in item_lower:
                return category
    
    return 'Miscellaneous'

def get_response_text(lang, message_type, **kwargs):
    """Get localized response text"""
    responses = {
        'english': {
            'understood': "Got it! Let me process that expense...",
            'missing_amount': "I couldn't find the amount. How much did you spend?",
            'missing_item': "What did you buy or pay for?",
            'confirm': "Should I save this to your Daily Log?",
            'saved': "✅ Expense saved!",
            'cancelled': "Okay, expense not saved.",
        },
        'tagalog': {
            'understood': "Naintindihan ko! Ipoproseso ko ang gastos mo...",
            'missing_amount': "Hindi ko makita ang halaga. Magkano ang ginastos mo?",
            'missing_item': "Ano ang binili o binayaran mo?",
            'confirm': "I-save ko ba ito sa iyong Daily Log?",
            'saved': "✅ Na-save na ang gastos!",
            'cancelled': "Sige, hindi na-save.",
        },
        'bisaya': {
            'understood': "Nakasabot ko! Iproseso nako ni...",
            'missing_amount': "Wala koy makita nga kantidad. Pila man ang imong gigasto?",
            'missing_item': "Unsa man ang imong gipalit o gibayaran?",
            'confirm': "I-save ba nako ni sa imong Daily Log?",
            'saved': "✅ Na-save na!",
            'cancelled': "Sige, wala na-save.",
        }
    }
    
    return responses[lang].get(message_type, "")

def process_expense_input(user_input):
    """Process user input and extract expense data"""
    # Step 1: Language Detection
    detected_lang = detect_language(user_input)
    
    # Step 2: Data Extraction
    amount = extract_amount(user_input)
    item = extract_item(user_input, amount)
    
    # Check for missing data
    if amount is None:
        return {
            'status': 'missing_amount',
            'language': detected_lang,
            'message': get_response_text(detected_lang, 'missing_amount')
        }
    
    if item is None or item == '':
        return {
            'status': 'missing_item',
            'language': detected_lang,
            'amount': amount,
            'message': get_response_text(detected_lang, 'missing_item')
        }
    
    # Step 3: Categorize
    category = categorize_item(item)
    
    return {
        'status': 'ready',
        'language': detected_lang,
        'amount': amount,
        'item': item,
        'category': category,
        'message': get_response_text(detected_lang, 'understood')
    }

def calculate_total():
    """Calculate total expenses"""
    if not st.session_state.expenses:
        return 0
    return sum(exp['amount'] for exp in st.session_state.expenses)

# App Header
st.title("💰 Resibo")
st.caption("Your Multilingual Expense Tracker | English • Tagalog • Bisaya")

# Sidebar - Daily Log
with st.sidebar:
    st.header("📊 Daily Log")
    
    if st.session_state.expenses:
        df = pd.DataFrame(st.session_state.expenses)
        
        # Display total
        total = calculate_total()
        st.metric("Total Expenses", f"₱{total:,.2f}")
        
        # Export to CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"resibo_expenses_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.divider()
        
        # Category breakdown
        st.subheader("By Category")
        category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        for cat, amt in category_totals.items():
            percentage = (amt / total) * 100
            st.write(f"**{cat}:** ₱{amt:,.2f} ({percentage:.1f}%)")
        
        st.divider()
        
        # Expense list
        st.subheader("All Expenses")
        for i, exp in enumerate(reversed(st.session_state.expenses)):
            with st.expander(f"₱{exp['amount']} - {exp['item']}"):
                st.write(f"**Category:** {exp['category']}")
                st.write(f"**Time:** {exp['timestamp']}")
        
        # Clear button
        if st.button("🗑️ Clear All", type="secondary"):
            st.session_state.expenses = []
            st.session_state.pending_expense = None
            st.rerun()
    else:
        st.info("No expenses logged yet. Start chatting below!")
    
    st.divider()
    
    # Category Management Section
    st.subheader("🏷️ Manage Categories")
    
    with st.expander("➕ Add Custom Category"):
        new_cat_name = st.text_input("Category Name", placeholder="e.g., Pets, Subscriptions")
        new_cat_keywords = st.text_input("Keywords (comma-separated)", 
                                         placeholder="e.g., dog food, vet, pet")
        
        if st.button("Add Category"):
            if new_cat_name and new_cat_keywords:
                keywords_list = [k.strip() for k in new_cat_keywords.split(',')]
                st.session_state.custom_categories[new_cat_name] = keywords_list
                st.success(f"✅ Added category: {new_cat_name}")
                st.rerun()
            else:
                st.error("Please fill in both fields")
    
    # Show existing custom categories
    if st.session_state.custom_categories:
        st.write("**Your Custom Categories:**")
        for cat, keywords in st.session_state.custom_categories.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"**{cat}:** {', '.join(keywords[:3])}")
            with col2:
                if st.button("🗑️", key=f"del_{cat}"):
                    del st.session_state.custom_categories[cat]
                    st.rerun()
    
    # Show default categories
    with st.expander("📋 Default Categories"):
        default_cats = list(CATEGORY_KEYWORDS.keys())
        for cat in default_cats:
            if cat != 'Miscellaneous':
                st.write(f"• {cat}")
        st.caption("Miscellaneous (catch-all)")

# Main Chat Interface
st.subheader("💬 Chat to Log Expenses")

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg['role']):
        st.write(msg['content'])

# Chat input
user_input = st.chat_input("Type your expense (e.g., 'I bought lunch for 85 pesos' or 'Plete nako 20')")

if user_input:
    # Add user message to chat
    st.session_state.chat_history.append({'role': 'user', 'content': user_input})
    
    # Process input
    result = process_expense_input(user_input)
    
    if result['status'] == 'ready':
        # Store pending expense
        st.session_state.pending_expense = result
        
        # Create response message
        response = f"{result['message']}\n\n"
        response += "**Expense Summary:**\n\n"
        response += f"| Field | Value |\n"
        response += f"|-------|-------|\n"
        response += f"| Amount | ₱{result['amount']:,.2f} |\n"
        response += f"| Item | {result['item']} |\n"
        response += f"| Category | {result['category']} |\n\n"
        response += get_response_text(result['language'], 'confirm')
        
        st.session_state.chat_history.append({'role': 'assistant', 'content': response})
        
    else:
        # Missing data - ask for clarification
        st.session_state.chat_history.append({'role': 'assistant', 'content': result['message']})
    
    st.rerun()

# Confirmation buttons (only show if there's a pending expense)
if st.session_state.pending_expense:
    st.divider()
    
    # Show current category and allow override
    exp = st.session_state.pending_expense
    
    # Get all available categories
    all_categories = list(CATEGORY_KEYWORDS.keys()) + list(st.session_state.custom_categories.keys())
    all_categories = sorted(set(all_categories))  # Remove duplicates and sort
    
    # Find current category index
    current_idx = all_categories.index(exp['category']) if exp['category'] in all_categories else 0
    
    selected_category = st.selectbox(
        "📂 Category (you can change it):",
        options=all_categories,
        index=current_idx,
        key="category_override"
    )
    
    # Update pending expense category if changed
    if selected_category != exp['category']:
        st.session_state.pending_expense['category'] = selected_category
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Yes, Save", type="primary", use_container_width=True):
            exp = st.session_state.pending_expense
            st.session_state.expenses.append({
                'amount': exp['amount'],
                'item': exp['item'],
                'category': exp['category'],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Add confirmation message
            total = calculate_total()
            confirm_msg = f"{get_response_text(exp['language'], 'saved')} Running total: ₱{total:,.2f}"
            st.session_state.chat_history.append({'role': 'assistant', 'content': confirm_msg})
            
            st.session_state.pending_expense = None
            st.rerun()
    
    with col2:
        if st.button("❌ No, Cancel", use_container_width=True):
            exp = st.session_state.pending_expense
            cancel_msg = get_response_text(exp['language'], 'cancelled')
            st.session_state.chat_history.append({'role': 'assistant', 'content': cancel_msg})
            
            st.session_state.pending_expense = None
            st.rerun()

# Footer
st.divider()
st.caption("💡 Tip: Just type naturally! Examples: 'Bumili ako ng bigas 200' | 'Plete nako 15' | 'Coffee 50 pesos'")
