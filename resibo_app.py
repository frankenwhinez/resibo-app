import streamlit as st
import pandas as pd
from datetime import datetime
import re
import random

# Page configuration
st.set_page_config(
    page_title="Resibo - Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Airbnb-inspired design
st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark mode colors */
    :root {
        --bg-primary: #0F1419;
        --bg-surface: #1A1F26;
        --bg-elevated: #242B33;
        --border-color: #2D3339;
        --text-primary: #FFFFFF;
        --text-secondary: #8E949E;
        --accent: #10B981;
        --accent-hover: #059669;
    }
    
    /* Main container */
    .main {
        background-color: var(--bg-primary);
        padding: 0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--bg-surface);
        border-right: 1px solid var(--border-color);
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"] .element-container {
        padding: 0.5rem 1rem;
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Card style */
    .card {
        background-color: var(--bg-surface);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    /* Chat message styles */
    .user-message {
        background-color: var(--bg-elevated);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        margin-left: auto;
        max-width: 70%;
        text-align: right;
        color: var(--text-primary);
    }
    
    .assistant-message {
        background-color: var(--bg-surface);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        max-width: 70%;
        border-left: 3px solid var(--accent);
        color: var(--text-primary);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--accent);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: var(--accent-hover);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    /* Input box */
    .stTextInput > div > div > input {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        padding: 0.75rem 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--accent);
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 700;
    }
    
    /* Text */
    p, span, div {
        color: var(--text-secondary);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--bg-surface);
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    /* Fixed chat input container */
    .fixed-chat-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: var(--bg-primary);
        padding: 1rem;
        border-top: 1px solid var(--border-color);
        z-index: 999;
        box-shadow: 0 -4px 12px rgba(0,0,0,0.4);
    }
    
    /* Welcome card */
    .welcome-card {
        background: linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-elevated) 100%);
        border-radius: 16px;
        padding: 3rem 2rem;
        text-align: center;
        border: 1px solid var(--border-color);
        margin: 2rem 0;
    }
    
    .welcome-title {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 1rem;
    }
    
    .welcome-subtitle {
        font-size: 1.1rem;
        color: var(--text-secondary);
        margin-bottom: 2rem;
    }
    
    .feature-list {
        text-align: left;
        max-width: 500px;
        margin: 0 auto;
    }
    
    .feature-item {
        display: flex;
        align-items: center;
        padding: 0.5rem 0;
        color: var(--text-primary);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
if 'pending_expense' not in st.session_state:
    st.session_state.pending_expense = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'custom_categories' not in st.session_state:
    st.session_state.custom_categories = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'show_load_more' not in st.session_state:
    st.session_state.show_load_more = False
if 'messages_to_show' not in st.session_state:
    st.session_state.messages_to_show = 10

# Language detection keywords
LANGUAGE_PATTERNS = {
    'tagalog': ['bumili', 'binili', 'binayad', 'bayad', 'gastos', 'gumastos', 'nagbayad'],
    'bisaya': ['plete', 'palit', 'gipalit', 'gibayad', 'bayad', 'gasto']
}

# Category keywords for auto-classification
CATEGORY_KEYWORDS = {
    'Food & Dining': [
        'food', 'meal', 'lunch', 'dinner', 'breakfast', 'snack', 'merienda',
        'rice', 'bigas', 'ulam', 'kaon', 'pagkaon', 'sud-an',
        'restaurant', 'jollibee', 'mcdo', 'mcdonald', 'kfc', 'pizza', 'burger',
        'coffee', 'kape', 'starbucks', 'cafe', 'carinderia', 'turo-turo',
        'grocery', 'groceries', 'palengke', 'market', 'supermarket', 'sari-sari',
        'vegetables', 'gulay', 'meat', 'karne', 'fish', 'isda', 'fruits', 'prutas', 'egg', 'itlog'
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
    cleaned = re.sub(r'₱?\d+(?:\.\d+)?\s*(?:pesos?|php)?', '', text, flags=re.IGNORECASE)
    
    remove_words = ['bumili', 'binili', 'bought', 'paid', 'for', 'ako', 'ng', 'sa', 'nako', 'ko', 
                    'gipalit', 'gibayad', 'spent', 'halagang', 'kay', 'og']
    
    for word in remove_words:
        cleaned = re.sub(r'\b' + word + r'\b', '', cleaned, flags=re.IGNORECASE)
    
    cleaned = ' '.join(cleaned.split()).strip()
    
    return cleaned if cleaned else None

def categorize_item(item_text):
    """Auto-assign category based on item keywords"""
    if not item_text:
        return 'Miscellaneous'
    
    item_lower = item_text.lower()
    
    # First check custom categories
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

def get_response_text(lang, message_type):
    """Get localized response text"""
    responses = {
        'english': {
            'missing_amount': "I couldn't find the amount. How much did you spend?",
            'missing_item': "What did you buy or pay for?",
            'confirm': "Should I save this?",
            'saved': "✅ Saved!",
            'cancelled': "Okay, not saved.",
        },
        'tagalog': {
            'missing_amount': "Hindi ko makita ang halaga. Magkano ang ginastos mo?",
            'missing_item': "Ano ang binili o binayaran mo?",
            'confirm': "I-save ko ba ito?",
            'saved': "✅ Na-save na!",
            'cancelled': "Sige, hindi na-save.",
        },
        'bisaya': {
            'missing_amount': "Wala koy makita nga kantidad. Pila man ang imong gigasto?",
            'missing_item': "Unsa man ang imong gipalit o gibayaran?",
            'confirm': "I-save ba nako ni?",
            'saved': "✅ Na-save na!",
            'cancelled': "Sige, wala na-save.",
        }
    }
    
    return responses[lang].get(message_type, "")

def calculate_total():
    """Calculate total expenses"""
    if not st.session_state.expenses:
        return 0
    return sum(exp['amount'] for exp in st.session_state.expenses)

def generate_conversational_confirmation(item, category, amount):
    """Generate conversational confirmation message"""
    
    category_emoji = {
        'Food & Dining': '🍽️',
        'Transport': '🚕',
        'Shopping': '🛍️',
        'Bills & Utilities': '💡',
        'Entertainment': '🎮',
        'Health & Wellness': '💊',
        'Personal Care': '💇',
        'Education': '📚',
        'Gifts & Others': '🎁',
        'Miscellaneous': '🗂️'
    }
    
    emoji = category_emoji.get(category, '📝')
    
    # Main confirmation
    confirmation = f"Copy that! Listed **₱{amount:,.2f}** under **{category}**. {emoji}"
    
    # Contextual witty comment
    witty_comments = {
        'Food & Dining': [
            f"Itong \"{item}\" ba talaga yan? 😅",
            "Busog ka na? 😋",
            "Sarap nyan! 🤤",
            "Kumain na ba? 🍴"
        ],
        'Transport': [
            "Saan ka galing? 🛣️",
            "Malayo ba byahe? 🚗",
            "Traffic ba? 😅",
            "Mahal na plete ngayon! 💸"
        ],
        'Shopping': [
            "Need ba talaga yan? 😂",
            "Sale ba to? 🏷️",
            "Bagong bili! ✨",
            "Shopping therapy? 💳"
        ],
        'Bills & Utilities': [
            "Bayad muna bago gala! 💪",
            "Adulting mode ON! 🎯",
            "Responsible naman! 👏",
            "No disconnection today! ✅"
        ],
        'Entertainment': [
            "Enjoy mode activated! 🎉",
            "You deserve it! ✨",
            "Happy ka naman? 😊",
            "Life is short! 🌟"
        ],
        'Health & Wellness': [
            "Health is wealth! 💪",
            "Alagaan ang sarili! 🌡️",
            "Investment yan! 💯",
            "Get well soon! 🏥"
        ],
        'Personal Care': [
            "Pampaganda/poganda! ✨",
            "Self-care is important! 💅",
            "Bagong look? 😊",
            "Treat yourself! 🧖"
        ],
        'Education': [
            "Brain gains! 🧠",
            "Keep learning! 🎓",
            "Future-proofing! 💡",
            "Knowledge is power! 📖"
        ],
        'Gifts & Others': [
            "Mabait ka naman! 🎁",
            "Good karma yan! ✨",
            "Generous! 💝",
            "Blessing others! 🙏"
        ],
        'Miscellaneous': [
            f"Itong \"{item}\" noted! 📝",
            "Saved! ✅",
            "Got it! 👍",
            "Copy that! 📋"
        ]
    }
    
    # Special case for high amounts
    if amount >= 1000:
        comments = [
            f"Whoa! ₱{amount:,.0f}?! Big purchase yarn! 😮",
            f"Worth it ba? 🤔",
            "Big one! 💸"
        ]
        comment = random.choice(comments)
    else:
        comments = witty_comments.get(category, witty_comments['Miscellaneous'])
        comment = random.choice(comments)
    
    return confirmation, comment

def generate_spending_insights(df, total):
    """Generate AI-powered insights"""
    
    category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)
    top_category = category_totals.index[0]
    top_category_amount = category_totals.iloc[0]
    top_category_pct = (top_category_amount / total) * 100
    
    num_expenses = len(df)
    avg_expense = total / num_expenses
    
    category_counts = df['category'].value_counts()
    most_frequent_category = category_counts.index[0]
    most_frequent_count = category_counts.iloc[0]
    
    largest_expense = df.loc[df['amount'].idxmax()]
    
    insights = f"""
**Overview:**
You've logged **{num_expenses} expenses** totaling **₱{total:,.2f}**. Your average expense is **₱{avg_expense:,.2f}**.

**🎯 Top Spending Category:**
Your biggest spending area is **{top_category}** at **₱{top_category_amount:,.2f}** ({top_category_pct:.1f}% of total). 
"""
    
    category_advice = {
        'Food & Dining': "💡 **Tip:** Food takes up a large portion of your budget. Consider meal prepping or cooking at home more often to save money!",
        'Transport': "💡 **Tip:** Transport costs add up quickly. Consider carpooling, using public transport, or planning your trips to minimize travel expenses.",
        'Shopping': "💡 **Tip:** Shopping is your top expense. Try the 24-hour rule: wait a day before buying non-essentials to avoid impulse purchases.",
        'Bills & Utilities': "💡 **Tip:** Bills are essential but check if you can optimize—compare internet/mobile plans, or save electricity with energy-efficient habits.",
        'Entertainment': "💡 **Tip:** Entertainment spending is high. Look for free alternatives like parks, free events, or share subscriptions with friends/family.",
        'Health & Wellness': "💡 **Tip:** Health is important! Consider generic medicines when possible, and use health insurance benefits to reduce costs.",
        'Personal Care': "💡 **Tip:** Personal care matters, but check if you can DIY some services or find affordable alternatives.",
        'Education': "💡 **Tip:** Education is an investment! Look for free online courses, second-hand books, or library resources to reduce costs.",
    }
    
    if top_category in category_advice:
        insights += f"\n{category_advice[top_category]}\n"
    
    insights += f"""
**📊 Spending Behavior:**
You spend most frequently on **{most_frequent_category}** ({most_frequent_count} transactions). 
"""
    
    top_3_pct = (category_totals.head(3).sum() / total) * 100
    if top_3_pct > 70:
        insights += f"\n**🔍 Pattern Alert:** {top_3_pct:.0f}% of your spending is concentrated in just 3 categories. Consider if this balance aligns with your priorities."
    else:
        insights += f"\n**✅ Balanced Spending:** Your expenses are well-distributed across {len(category_totals)} categories."
    
    insights += f"""

**🏆 Biggest Single Expense:**
₱{largest_expense['amount']:,.2f} on **{largest_expense['item']}** ({largest_expense['category']})
"""
    
    if num_expenses >= 10:
        insights += "\n\n**🎉 Great job tracking!** You're building great financial awareness by consistently logging your expenses. Keep it up!"
    elif num_expenses >= 5:
        insights += "\n\n**👍 Good start!** Keep logging expenses to get more detailed insights and better understand your spending patterns."
    
    return insights

def process_expense_input(user_input):
    """Process user input and extract expense data"""
    detected_lang = detect_language(user_input)
    
    amount = extract_amount(user_input)
    item = extract_item(user_input, amount)
    
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
    
    category = categorize_item(item)
    
    return {
        'status': 'ready',
        'language': detected_lang,
        'amount': amount,
        'item': item,
        'category': category
    }

# Sidebar
with st.sidebar:
    st.markdown("### 💰 Resibo")
    st.markdown("---")
    
    # Navigation
    if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.current_page == 'home' else "secondary"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    if st.button("💬 Log Expenses", use_container_width=True, type="primary" if st.session_state.current_page == 'log' else "secondary"):
        st.session_state.current_page = 'log'
        st.rerun()
    
    if st.button("📊 Analytics", use_container_width=True, type="primary" if st.session_state.current_page == 'analytics' else "secondary"):
        st.session_state.current_page = 'analytics'
        st.rerun()
    
    if st.button("⚙️ Settings", use_container_width=True, type="primary" if st.session_state.current_page == 'settings' else "secondary"):
        st.session_state.current_page = 'settings'
        st.rerun()
    
    st.markdown("---")
    
    # Daily Log Summary
    st.markdown("### 📊 Today's Summary")
    
    if st.session_state.expenses:
        total = calculate_total()
        st.metric("Total Spent", f"₱{total:,.2f}")
        
        df = pd.DataFrame(st.session_state.expenses)
        category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False).head(3)
        
        st.markdown("**Top Categories:**")
        for cat, amt in category_totals.items():
            st.markdown(f"• {cat}: ₱{amt:,.2f}")
        
        st.markdown("**Recent:**")
        for exp in list(reversed(st.session_state.expenses))[:3]:
            st.markdown(f"• ₱{exp['amount']:,.0f} - {exp['item']}")
        
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.expenses = []
            st.session_state.chat_history = []
            st.session_state.pending_expense = None
            st.rerun()
    else:
        st.info("No expenses yet!")

# Main content area
if st.session_state.current_page == 'home':
    st.markdown("""
    <div class="welcome-card">
        <div class="welcome-title">Track. Analyze. Save. 💰</div>
        <div class="welcome-subtitle">Your multilingual budget companion</div>
        <div class="feature-list">
            <div class="feature-item">✅ Natural language logging</div>
            <div class="feature-item">✅ AI-powered insights</div>
            <div class="feature-item">✅ Taglish supported</div>
        </div>
        <p style="margin-top: 2rem; color: var(--text-secondary);">
            Start by clicking <strong>💬 Log Expenses</strong> in the sidebar!
        </p>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.current_page == 'log':
    st.markdown("### 💬 Log Your Expenses")
    st.markdown("Type naturally - 'Lunch 85 pesos', 'Plete nako 15', 'Bumili bigas 200'")
    
    # Chat history with load more
    messages_to_display = st.session_state.chat_history[-st.session_state.messages_to_show:]
    
    if len(st.session_state.chat_history) > st.session_state.messages_to_show:
        if st.button("↑ Load earlier messages"):
            st.session_state.messages_to_show += 10
            st.rerun()
    
    for msg in messages_to_display:
        if msg['role'] == 'user':
            st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)
    
    # Pending expense confirmation (conversational format)
    if st.session_state.pending_expense:
        exp = st.session_state.pending_expense
        
        confirmation, comment = generate_conversational_confirmation(
            exp['item'], 
            exp['category'], 
            exp['amount']
        )
        
        st.markdown(f"""
        <div class="card">
            <p style="color: var(--text-primary); font-size: 1.1rem; margin-bottom: 1rem;">
                {confirmation}
            </p>
            <p style="color: var(--text-secondary); font-size: 1rem; margin-bottom: 1.5rem;">
                {comment}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("📂 **Category** (you can change it):")
        
        all_categories = list(CATEGORY_KEYWORDS.keys()) + list(st.session_state.custom_categories.keys())
        all_categories = sorted(set(all_categories))
        
        current_idx = all_categories.index(exp['category']) if exp['category'] in all_categories else 0
        
        selected_category = st.selectbox(
            "Select category",
            options=all_categories,
            index=current_idx,
            key="category_override",
            label_visibility="collapsed"
        )
        
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
    
    # Chat input
    st.markdown("<br><br>", unsafe_allow_html=True)
    user_input = st.text_input(
        "Type your expense...",
        placeholder="e.g., 'I bought lunch for 85 pesos' or 'Plete nako 20'",
        key="expense_input",
        label_visibility="collapsed"
    )
    
    if user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        result = process_expense_input(user_input)
        
        if result['status'] == 'ready':
            st.session_state.pending_expense = result
        else:
            st.session_state.chat_history.append({'role': 'assistant', 'content': result['message']})
        
        st.rerun()

elif st.session_state.current_page == 'analytics':
    st.markdown("### 📊 Analytics & Insights")
    
    if not st.session_state.expenses:
        st.info("📊 No expenses yet! Start logging in the Log Expenses tab to see your analytics here.")
    else:
        df = pd.DataFrame(st.session_state.expenses)
        total = calculate_total()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Spent", f"₱{total:,.2f}")
        with col2:
            st.metric("Total Expenses", len(st.session_state.expenses))
        with col3:
            avg_expense = total / len(st.session_state.expenses)
            st.metric("Avg per Expense", f"₱{avg_expense:,.2f}")
        
        st.markdown("---")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### 📊 Spending by Category")
            category_totals = df.groupby('category')['amount'].sum().reset_index()
            category_totals.columns = ['Category', 'Amount']
            
            import plotly.express as px
            fig_pie = px.pie(
                category_totals, 
                values='Amount', 
                names='Category',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(showlegend=False, height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with chart_col2:
            st.markdown("#### 📈 Top Spending Categories")
            top_categories = category_totals.sort_values('Amount', ascending=False).head(5)
            
            fig_bar = px.bar(
                top_categories,
                x='Amount',
                y='Category',
                orientation='h',
                color='Amount',
                color_continuous_scale='Greens'
            )
            fig_bar.update_layout(
                showlegend=False,
                height=350,
                yaxis={'categoryorder': 'total ascending'},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            fig_bar.update_traces(text=top_categories['Amount'].apply(lambda x: f"₱{x:,.0f}"), textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown("---")
        
        st.markdown("#### 🤖 AI Spending Insights")
        
        with st.expander("💡 Your Personalized Analysis", expanded=True):
            insights = generate_spending_insights(df, total)
            st.markdown(insights)
            
            if st.button("🔄 Refresh Insights", use_container_width=True):
                st.rerun()

elif st.session_state.current_page == 'settings':
    st.markdown("### ⚙️ Settings")
    
    st.markdown("#### 🏷️ Manage Categories")
    
    with st.expander("➕ Add Custom Category"):
        new_cat_name = st.text_input("Category Name", placeholder="e.g., Pets, Subscriptions")
        new_cat_keywords = st.text_input("Keywords (comma-separated)", 
                                         placeholder="e.g., dog food, vet, pet")
        
        if st.button("Add Category", use_container_width=True):
            if new_cat_name and new_cat_keywords:
                keywords_list = [k.strip() for k in new_cat_keywords.split(',')]
                st.session_state.custom_categories[new_cat_name] = keywords_list
                st.success(f"✅ Added category: {new_cat_name}")
                st.rerun()
            else:
                st.error("Please fill in both fields")
    
    if st.session_state.custom_categories:
        st.markdown("**Your Custom Categories:**")
        for cat, keywords in st.session_state.custom_categories.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{cat}:** {', '.join(keywords[:3])}")
            with col2:
                if st.button("🗑️", key=f"del_{cat}"):
                    del st.session_state.custom_categories[cat]
                    st.rerun()
    
    with st.expander("📋 Default Categories"):
        for cat in CATEGORY_KEYWORDS.keys():
            if cat != 'Miscellaneous':
                st.markdown(f"• {cat}")
        st.caption("Miscellaneous (catch-all)")
    
    st.markdown("---")
    
    if st.session_state.expenses:
        st.markdown("#### 📥 Export Data")
        df = pd.DataFrame(st.session_state.expenses)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"resibo_expenses_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
