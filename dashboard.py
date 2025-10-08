import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import numpy as np
from src.agent import WaterIntakeAgent
from src.database import log_intake, get_intake_history, get_daily_total
import sqlite3
import os

DB_NAME = 'water_tracker.db'

# Page configuration
st.set_page_config(
    page_title="AI Water Tracker 💧",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(45deg, #00B4DB, #0083B0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .feedback-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .warning-card {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Data validation and cleanup functions
def validate_intake_data(history, max_reasonable_intake=5000):
    """Validate intake data and filter out unrealistic values"""
    if not history:
        return []
    
    valid_data = []
    for row in history:
        if len(row) >= 2:  # Ensure row has at least 2 elements
            date_str, intake_ml = row[0], row[1]
            if intake_ml <= max_reasonable_intake:  # Maximum 5L per entry is reasonable
                valid_data.append((date_str, intake_ml))
            else:
                st.warning(f"⚠️ Filtered out unrealistic entry: {intake_ml}ml on {date_str}")
    
    return valid_data

def get_validated_intake_history(user_id):
    """Get intake history with data validation"""
    history = get_intake_history(user_id)
    return validate_intake_data(history)

def get_validated_daily_total(user_id, date=None):
    """Get daily total with data validation"""
    if date is None:
        date = datetime.today().strftime('%Y-%m-%d')
    
    history = get_intake_history(user_id)
    valid_history = validate_intake_data(history)
    
    # Calculate total for today from validated data only
    today_total = 0
    for date_str, intake_ml in valid_history:
        if date_str == date:
            today_total += intake_ml
    
    return min(today_total, 10000)  # Cap at 10L per day maximum

def cleanup_unrealistic_data(user_id, max_reasonable_intake=5000):
    """Remove unrealistic data entries from database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Delete entries with unrealistic intake values
        cursor.execute(
            "DELETE FROM water_intake WHERE user_id = ? AND intake_ml > ?",
            (user_id, max_reasonable_intake)
        )
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count > 0:
            st.success(f"🧹 Cleaned up {deleted_count} unrealistic entries!")
        
        return deleted_count
    except sqlite3.Error as e:
        st.error(f"Error cleaning data: {e}")
        return 0
    finally:
        conn.close()

def reset_user_data(user_id):
    """Completely reset user data"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM water_intake WHERE user_id = ?",
            (user_id,)
        )
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count > 0:
            st.success(f"🔄 Reset complete! Removed {deleted_count} entries for user {user_id}")
        
        return deleted_count
    except sqlite3.Error as e:
        st.error(f"Error resetting data: {e}")
        return 0
    finally:
        conn.close()

if "tracker_started" not in st.session_state:
    st.session_state.tracker_started = False

# Welcome section
if not st.session_state.tracker_started:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 class="main-header">💧 AI Water Tracker</h1>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 20px; color: white; box-shadow: 0 8px 16px rgba(0,0,0,0.2);'>
            <h2 style='color: white; margin-bottom: 1rem;'>Stay Hydrated, Stay Healthy 🚀</h2>
            <p style='font-size: 1.2rem; margin-bottom: 1.5rem;'>
                Track your daily hydration with our AI assistant. Get personalized feedback, 
                visualize your progress, and build healthy habits that last!
            </p>
            <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 2rem 0;'>
                <div style='text-align: center;'>
                    <h3>📊</h3>
                    <p>Smart Analytics</p>
                </div>
                <div style='text-align: center;'>
                    <h3>🤖</h3>
                    <p>AI Feedback</p>
                </div>
                <div style='text-align: center;'>
                    <h3>📈</h3>
                    <p>Progress Tracking</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Your Hydration Journey", use_container_width=True, type="primary"):
            st.session_state.tracker_started = True
            st.rerun()

else:
    # Main Dashboard
    st.markdown('<h1 class="main-header">💧 AI Water Tracker Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #00B4DB, #0083B0); 
                    border-radius: 10px; color: white; margin-bottom: 2rem;'>
            <h3>💧 Log Water Intake</h3>
        </div>
        """, unsafe_allow_html=True)
        
        user_id = st.text_input("👤 User ID", value="user_123", help="Enter your unique user identifier")
        
        # Data management section
        with st.expander("⚙️ Data Management"):
            st.write("Manage your water intake data:")
            
            if st.button("🧹 Clean Unrealistic Data", use_container_width=True):
                if user_id:
                    cleaned_count = cleanup_unrealistic_data(user_id)
                    if cleaned_count == 0:
                        st.info("No unrealistic data found! ✅")
                    st.rerun()
            
            if st.button("🔄 Reset All Data", use_container_width=True):
                if user_id:
                    if st.checkbox("I'm sure I want to delete all my data"):
                        reset_user_data(user_id)
                        st.rerun()
        
        st.markdown("### Quick Log")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🥛 250ml", use_container_width=True):
                intake_ml = 250
                if user_id:
                    log_intake(user_id, intake_ml)
                    st.success(f"Logged 250ml! 💧")
                    st.rerun()
        with col2:
            if st.button("💧 500ml", use_container_width=True):
                intake_ml = 500
                if user_id:
                    log_intake(user_id, intake_ml)
                    st.success(f"Logged 500ml! 💦")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### Custom Amount")
        intake_ml = st.number_input("Water Intake (ml)", min_value=0, max_value=5000, step=50, value=500,
                                   help="Maximum reasonable intake: 5000ml (5L) per entry")
        
        if st.button("✅ Log Intake", use_container_width=True, type="primary"):
            if user_id and intake_ml > 0:
                if intake_ml > 5000:
                    st.error("❌ That's too much water at once! Maximum 5000ml per entry.")
                else:
                    success = log_intake(user_id, intake_ml)
                    if success:
                        st.balloons()
                        st.success(f"Successfully logged {intake_ml}ml! 🎉")
                        st.rerun()
                    else:
                        st.error("Failed to log intake. Please try again.")

    # Main content area
    if user_id:
        # Get VALIDATED history data
        history = get_validated_intake_history(user_id)
        today_total = get_validated_daily_total(user_id)
        
        # Check for data quality issues
        raw_history = get_intake_history(user_id)
        if len(raw_history) > len(history):
            st.markdown(f"""
            <div class="warning-card">
                <h3>⚠️ Data Quality Alert</h3>
                <p>Found {len(raw_history) - len(history)} unrealistic entries in your data.</p>
                <p>Use the "Clean Unrealistic Data" button in the sidebar to fix this.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Top Metrics Row with reasonable limits
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Today's Total (capped at reasonable maximum)
            display_today = min(today_total, 10000)  # Cap display at 10L
            st.markdown(f"""
            <div class="metric-card">
                <h3>Today's Total</h3>
                <h2>{display_today} ml</h2>
                <p>💧 Daily Intake</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Average (calculated from validated data only)
            if history:
                avg_intake = np.mean([row[1] for row in history])
                display_avg = min(avg_intake, 5000)  # Cap at 5L for display
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Average</h3>
                    <h2>{display_avg:.0f} ml</h2>
                    <p>📊 Daily Average</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="metric-card">
                    <h3>Average</h3>
                    <h2>0 ml</h2>
                    <p>📊 Daily Average</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            # Tracking Days
            if history:
                unique_dates = set([row[0] for row in history])
                total_days = len(unique_dates)
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Tracking Days</h3>
                    <h2>{total_days}</h2>
                    <p>📅 Days Tracked</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="metric-card">
                    <h3>Tracking Days</h3>
                    <h2>0</h2>
                    <p>📅 Days Tracked</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            # Daily Goal Progress
            goal = 2000  # Standard water intake goal
            progress = min(today_total / goal, 1.0)  # Cap at 100%
            st.markdown(f"""
            <div class="metric-card">
                <h3>Daily Goal</h3>
                <h2>{progress:.0%}</h2>
                <p>🎯 {min(today_total, goal)}/{goal} ml</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Visualization Section (using only validated data)
        if history:
            # Prepare data from validated history
            dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in history]
            values = [min(row[1], 5000) for row in history]  # Cap values for visualization
            
            df = pd.DataFrame({
                "Date": dates,
                "Water_Intake_ml": values,
                "Day": [date.strftime("%A") for date in dates]
            })
            
            # Group by date for daily totals (capped at reasonable maximum)
            daily_totals = df.groupby("Date")["Water_Intake_ml"].sum().reset_index()
            daily_totals["Water_Intake_ml"] = daily_totals["Water_Intake_ml"].apply(lambda x: min(x, 10000))
            
            # Create tabs for different visualizations
            tab1, tab2, tab3 = st.tabs(["📈 Trend Analysis", "📊 Daily Details", "🎯 Progress"])
            
            with tab1:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Line chart with Altair
                    st.subheader("Water Intake Trend")
                    chart = alt.Chart(daily_totals).mark_line(point=True).encode(
                        x='Date:T',
                        y=alt.Y('Water_Intake_ml:Q', scale=alt.Scale(domain=[0, 5000]), title="Water Intake (ml)"),
                        tooltip=['Date', 'Water_Intake_ml']
                    ).properties(
                        width=600,
                        height=400
                    )
                    # Add goal line
                    goal_line = alt.Chart(pd.DataFrame({'y': [2000]})).mark_rule(color='red', strokeDash=[5,5]).encode(y='y:Q')
                    st.altair_chart(chart + goal_line, use_container_width=True)
                
                with col2:
                    # Weekly summary
                    st.subheader("📅 Weekly Summary")
                    df_week = df[df["Date"] >= datetime.now() - timedelta(days=7)]
                    if not df_week.empty:
                        weekly_avg = df_week["Water_Intake_ml"].mean()
                        weekly_total = df_week["Water_Intake_ml"].sum()
                        
                        st.metric("Weekly Average", f"{weekly_avg:.0f} ml")
                        st.metric("Weekly Total", f"{weekly_total:.0f} ml")
                        st.metric("Days Tracked", len(df_week))
                    else:
                        st.info("No data for the past week")
            
            with tab2:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Recent activity table
                    st.subheader("📋 Recent Entries")
                    recent_df = df.sort_values("Date", ascending=False).head(10)
                    st.dataframe(recent_df, use_container_width=True)
                
                with col2:
                    # Statistics
                    st.subheader("📊 Statistics")
                    st.metric("Total Valid Entries", len(history))
                    st.metric("Maximum Single Entry", f"{df['Water_Intake_ml'].max():.0f} ml")
                    st.metric("Minimum Single Entry", f"{df['Water_Intake_ml'].min():.0f} ml")
            
            with tab3:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Progress visualization
                    st.subheader("Today's Progress")
                    goal = 2000
                    progress = min(today_total / goal, 1.0)
                    
                    st.metric("Current Intake", f"{today_total} ml")
                    st.progress(progress)
                    st.write(f"**{progress:.0%} towards daily goal of {goal} ml**")
                    
                    if today_total >= goal:
                        st.success("🎉 Daily Goal Achieved! You're doing amazing!")
                    elif today_total >= goal * 0.75:
                        st.warning("💪 Almost there! You're at 75% of your goal")
                    elif today_total >= goal * 0.5:
                        st.info("👍 Halfway there! Keep going!")
                    else:
                        st.error("🚰 Keep drinking! You're below 50% of your goal")
                
                with col2:
                    st.subheader("🏆 Achievements")
                    
                    if today_total >= goal:
                        st.success("🎉 Daily Goal Achieved!")
                    
                    if len(history) >= 7:
                        st.success("🔥 7-Day Streak!")
                    
                    if len(history) >= 30:
                        st.success("⭐ Monthly Tracker!")
                    
                    st.metric("Goal Progress", f"{today_total}/{goal} ml")

            # AI Feedback Section
            st.markdown("---")
            st.markdown("### 🤖 AI Health Assistant")
            
            if intake_ml > 0 and intake_ml <= 5000:  # Only get feedback for reasonable intakes
                try:
                    agent = WaterIntakeAgent()
                    feedback = agent.analyze_intake(intake_ml)
                    
                    st.markdown(f"""
                    <div class="feedback-card">
                        <h3>💡 Personalized Feedback</h3>
                        <p style='font-size: 1.1rem;'>{feedback}</p>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"AI feedback temporarily unavailable: {e}")
        
        else:
            # Empty state
            st.markdown("""
            <div style='text-align: center; padding: 4rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        border-radius: 20px; color: white;'>
                <h2>🚰 Ready to Start Tracking?</h2>
                <p style='font-size: 1.2rem;'>Log your first water intake using the sidebar to see your dashboard come to life!</p>
                <div style='font-size: 4rem; margin: 2rem 0;'>💧</div>
                <p>Your hydration journey starts with that first sip!</p>
            </div>
            """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 2rem;'>"
        "💧 Stay Hydrated • 🏃 Stay Healthy • 🤖 Powered by AI"
        "</div>",
        unsafe_allow_html=True
    )