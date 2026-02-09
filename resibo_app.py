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

def generate_witty_acknowledgment(item, category, amount, language):
    """Generate contextual, witty one-liners based on expense context"""
    import random
    
    # Count similar expenses in current session
    similar_count = sum(1 for exp in st.session_state.expenses 
                       if exp['category'] == category)
    
    # Get total spent in this category
    category_total = sum(exp['amount'] for exp in st.session_state.expenses 
                        if exp['category'] == category)
    
    # Taglish witty responses by category and context
    witty_responses = {
        'Food & Dining': [
            f"Noted! That's your {similar_count + 1}th food expense ngayong session 🍽️",
            f"Got it! ₱{amount:,.0f} for {item}. Kumain na ba talaga? 😄",
            f"Alright! Food fund at ₱{category_total + amount:,.0f} na this session 🍔",
            f"Sige! Masarap ba yan? 😋",
            f"Oki! Another {item} logged. Food is life nga naman 🥘",
            f"Copy! That's ₱{amount:,.0f} sa tiyan 😂",
            f"Roger! Busog goals ba? 🍜",
        ],
        'Transport': [
            f"Noted! Pang-{similar_count + 1} mong sakay today 🚕",
            f"Got it! ₱{amount:,.0f} sa byahe. Saan ka papunta? 🛣️",
            f"Alright! Transport budget at ₱{category_total + amount:,.0f} na 🚌",
            f"Copy! Malayo ba byahe? 🚗",
            f"Oki! Another plete logged. Mahal na gas ngayon eh 😅",
            f"Sige! That's ₱{amount:,.0f} sa wheels 🛵",
            f"Noted! Commute life is real 🚇",
        ],
        'Shopping': [
            f"Ayy shopping! Yan ha, {similar_count + 1} na this session 🛍️",
            f"Oops! ₱{amount:,.0f} for {item}. Need ba talaga yan? 😂",
            f"Sige sige! Shopping total at ₱{category_total + amount:,.0f} na ngayon 🛒",
            f"Noted! Retail therapy ba yan? 💳",
            f"Got it! Another {item} sa cart. Sale ba? 😄",
            f"Copy! ₱{amount:,.0f} sa bagong bili 🎁",
            f"Alright! Shopping mode activated 🛍️",
        ],
        'Bills & Utilities': [
            f"Noted! Bayad is life. Adulting mode ON 💡",
            f"Got it! ₱{amount:,.0f} para sa {item}. Responsible ka naman! 👏",
            f"Alright! Bill payment #{similar_count + 1} logged ✅",
            f"Copy! Bayad muna bago gala 💪",
            f"Oki! {item} paid. No disconnection today! 😅",
            f"Sige! ₱{amount:,.0f} sa bills. Adulting is expensive 💸",
            f"Noted! Utilities are done. Good job! 🎯",
        ],
        'Entertainment': [
            f"Nice! ₱{amount:,.0f} for fun. You deserve it! 🎉",
            f"Ohhh {item}! Enjoy mode activated 🎮",
            f"Alright! ₱{category_total + amount:,.0f} na sa entertainment ngayong session 🎬",
            f"Copy! Life is short, mag-enjoy din! 😄",
            f"Got it! {item} for the soul ✨",
            f"Noted! ₱{amount:,.0f} sa happiness fund 🎊",
            f"Sige! That's pampagood vibes right there 🎵",
        ],
        'Health & Wellness': [
            f"Good! Health is wealth nga naman 💊",
            f"Noted! ₱{amount:,.0f} for {item}. Alagaan ang sarili! 💪",
            f"Got it! Investment sa health yan 🏥",
            f"Copy! Magpagaling ka! Get well soon 🩺",
            f"Alright! Health expenses at ₱{category_total + amount:,.0f} na 💉",
            f"Oki! {item} logged. Health first! 🌡️",
            f"Sige! ₱{amount:,.0f} sa wellness. Worth it yan! 🧘",
        ],
        'Personal Care': [
            f"Ayy ganda! Self-care is important 💇",
            f"Noted! ₱{amount:,.0f} for {item}. Pampaganda/poganda! ✨",
            f"Got it! Invest in yourself rin 💅",
            f"Copy! Bagong look ba yan? 😊",
            f"Alright! Personal care fund at ₱{category_total + amount:,.0f} 💄",
            f"Oki! {item} logged. Treat yourself! 🧖",
            f"Sige! ₱{amount:,.0f} sa self-love 💖",
        ],
        'Education': [
            f"Nice! Education is investment 📚",
            f"Noted! ₱{amount:,.0f} for {item}. Keep learning! 🎓",
            f"Got it! Brain gains! 🧠",
            f"Copy! Knowledge is power nga naman 📖",
            f"Alright! Education fund at ₱{category_total + amount:,.0f} 🏫",
            f"Oki! {item} logged. Future-proofing! 💡",
            f"Sige! ₱{amount:,.0f} sa utak investment 🤓",
        ],
        'Gifts & Others': [
            f"Aww! Mabait ka naman 🎁",
            f"Noted! ₱{amount:,.0f} for {item}. Generous! 💝",
            f"Got it! Blessing others din 🙏",
            f"Copy! Good karma yan! ✨",
            f"Alright! Gifts total at ₱{category_total + amount:,.0f} 🎀",
            f"Oki! {item} logged. Share the love! 💕",
            f"Sige! ₱{amount:,.0f} sa pag-share ng blessing 🌟",
        ],
        'Miscellaneous': [
            f"Noted! ₱{amount:,.0f} for {item} 📝",
            f"Got it! Random expense logged ✅",
            f"Copy! Miscellaneous na naman 😄",
            f"Alright! {item} saved 💾",
            f"Oki! Another one sa log 📊",
            f"Sige! ₱{amount:,.0f} noted 🗒️",
            f"Noted! Expense #{len(st.session_state.expenses) + 1} 🔢",
        ]
    }
    
    # Special responses for high amounts
    if amount >= 1000:
        high_amount_responses = [
            f"Whoa! ₱{amount:,.0f}?! Big purchase yarn! 😮",
            f"Ayan! ₱{amount:,.0f} for {item}. Worth it ba? 🤔",
            f"Naks! ₱{amount:,.0f}! That's a big one 💸",
        ]
        if random.random() < 0.3:  # 30% chance for high amount response
            return random.choice(high_amount_responses)
    
    # Special responses for frequent same category
    if similar_count >= 2:
        frequent_responses = [
            f"Again?! That's your {similar_count + 1}th {category} na! 👀",
            f"Ayan na naman! ₱{category_total + amount:,.0f} na sa {category} ah 📈",
            f"Uyyy {similar_count + 1} times na sa {category}! 😂",
        ]
        if random.random() < 0.4:  # 40% chance for frequent response
            return random.choice(frequent_responses)
    
    # Default: pick from category-specific responses
    category_responses = witty_responses.get(category, witty_responses['Miscellaneous'])
    return random.choice(category_responses)

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

# Tab Navigation
tab1, tab2 = st.tabs(["💬 Chat & Log", "📊 Analytics & Insights"])

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

# Tab 1: Chat & Log Expenses
with tab1:
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
            
            # Generate witty acknowledgment
            witty_msg = generate_witty_acknowledgment(
                result['item'], 
                result['category'], 
                result['amount'],
                result['language']
            )
            
            # Create response message with witty acknowledgment
            response = f"{witty_msg}\n\n"
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

# Tab 2: Analytics & Insights
with tab2:
    if not st.session_state.expenses:
        st.info("📊 No expenses yet! Start logging in the Chat tab to see your analytics here.")
    else:
        df = pd.DataFrame(st.session_state.expenses)
        total = calculate_total()
        
        # Overview metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Spent", f"₱{total:,.2f}")
        with col2:
            st.metric("Total Expenses", len(st.session_state.expenses))
        with col3:
            avg_expense = total / len(st.session_state.expenses)
            st.metric("Avg per Expense", f"₱{avg_expense:,.2f}")
        
        st.divider()
        
        # Charts section
        chart_col1, chart_col2 = st.columns(2)
        
        # Pie Chart - Category Breakdown
        with chart_col1:
            st.subheader("📊 Spending by Category")
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
            fig_pie.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Bar Chart - Top Categories
        with chart_col2:
            st.subheader("📈 Top Spending Categories")
            top_categories = category_totals.sort_values('Amount', ascending=False).head(5)
            
            fig_bar = px.bar(
                top_categories,
                x='Amount',
                y='Category',
                orientation='h',
                color='Amount',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(
                showlegend=False,
                height=350,
                yaxis={'categoryorder': 'total ascending'}
            )
            fig_bar.update_traces(text=top_categories['Amount'].apply(lambda x: f"₱{x:,.0f}"), textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.divider()
        
        # AI Insights Section
        st.subheader("🤖 AI Spending Insights")
        
        with st.expander("💡 **Your Personalized Analysis**", expanded=True):
            # Generate AI insights
            insights = generate_spending_insights(df, total)
            
            # Display insights in a nice format
            st.markdown(insights)
            
            # Add a refresh button
            if st.button("🔄 Refresh Insights", use_container_width=True):
                st.rerun()
        
        st.divider()
        
        # Detailed breakdown
        st.subheader("📋 Detailed Breakdown")
        
        # Category breakdown table
        category_details = df.groupby('category').agg({
            'amount': ['sum', 'count', 'mean']
        }).reset_index()
        category_details.columns = ['Category', 'Total', 'Count', 'Average']
        category_details['Percentage'] = (category_details['Total'] / total * 100).round(1)
        category_details = category_details.sort_values('Total', ascending=False)
        
        # Format the dataframe
        category_details['Total'] = category_details['Total'].apply(lambda x: f"₱{x:,.2f}")
        category_details['Average'] = category_details['Average'].apply(lambda x: f"₱{x:,.2f}")
        category_details['Percentage'] = category_details['Percentage'].apply(lambda x: f"{x}%")
        
        st.dataframe(category_details, use_container_width=True, hide_index=True)

def generate_spending_insights(df, total):
    """Generate AI-powered insights about spending patterns"""
    
    # Calculate key metrics
    category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)
    top_category = category_totals.index[0]
    top_category_amount = category_totals.iloc[0]
    top_category_pct = (top_category_amount / total) * 100
    
    num_expenses = len(df)
    avg_expense = total / num_expenses
    
    # Find most frequent category
    category_counts = df['category'].value_counts()
    most_frequent_category = category_counts.index[0]
    most_frequent_count = category_counts.iloc[0]
    
    # Find largest single expense
    largest_expense = df.loc[df['amount'].idxmax()]
    
    # Build insight text
    insights = f"""
**Overview:**
You've logged **{num_expenses} expenses** totaling **₱{total:,.2f}**. Your average expense is **₱{avg_expense:,.2f}**.

**🎯 Top Spending Category:**
Your biggest spending area is **{top_category}** at **₱{top_category_amount:,.2f}** ({top_category_pct:.1f}% of total). 
"""
    
    # Add contextual advice based on top category
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
    
    # Add frequency insight
    insights += f"""
**📊 Spending Behavior:**
You spend most frequently on **{most_frequent_category}** ({most_frequent_count} transactions). 
"""
    
    # Identify if spending is concentrated or distributed
    top_3_pct = (category_totals.head(3).sum() / total) * 100
    if top_3_pct > 70:
        insights += f"\n**🔍 Pattern Alert:** {top_3_pct:.0f}% of your spending is concentrated in just 3 categories. Consider if this balance aligns with your priorities."
    else:
        insights += f"\n**✅ Balanced Spending:** Your expenses are well-distributed across {len(category_totals)} categories."
    
    # Largest expense callout
    insights += f"""

**🏆 Biggest Single Expense:**
₱{largest_expense['amount']:,.2f} on **{largest_expense['item']}** ({largest_expense['category']})
"""
    
    # Add encouragement
    if num_expenses >= 10:
        insights += "\n\n**🎉 Great job tracking!** You're building great financial awareness by consistently logging your expenses. Keep it up!"
    elif num_expenses >= 5:
        insights += "\n\n**👍 Good start!** Keep logging expenses to get more detailed insights and better understand your spending patterns."
    
    return insights
