import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
import json
import os

# Page configuration
st.set_page_config(page_title="Rich's Time Tracker", page_icon="⏰", layout="wide")

# File to store data
DATA_FILE = "time_logs.json"

# Initialize session state
if 'logs' not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            st.session_state.logs = json.load(f)
    else:
        st.session_state.logs = []

def save_logs():
    """Save logs to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(st.session_state.logs, f, indent=2)

def add_log(log_date, hours, description, project="", time_ranges=None):
    """Add a new time log entry"""
    new_log = {
        "date": log_date.strftime("%Y-%m-%d"),
        "hours": hours,
        "description": description,
        "project": project,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if time_ranges:
        new_log["time_ranges"] = time_ranges
    st.session_state.logs.append(new_log)
    save_logs()

def delete_log(index):
    """Delete a log entry"""
    st.session_state.logs.pop(index)
    save_logs()

def format_time_12hr(time_str):
    """Convert time string to 12-hour format with AM/PM"""
    try:
        # Handle both formats: "HH:MM" and "HH:MM AM/PM"
        if 'AM' in time_str or 'PM' in time_str:
            return time_str
        # Parse military time and convert
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        return time_obj.strftime("%I:%M %p")
    except:
        return time_str

def get_logs_df():
    """Convert logs to DataFrame"""
    if st.session_state.logs:
        df = pd.DataFrame(st.session_state.logs)
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values('date', ascending=False)
    return pd.DataFrame()

# Main app
st.title("⏰ Rich's Time Tracker")
st.markdown("Log your work hours and share with your boss")

# Sidebar for adding new entries
with st.sidebar:
    st.header("📝 Log New Entry")
    
    log_date = st.date_input("Date", value=date.today())
    
    # Option to choose between manual hours or time ranges
    input_method = st.radio("Input Method", ["⏰ Time Ranges", "⌚ Manual Hours"], horizontal=True)
    
    time_ranges = []
    total_hours = 0.0
    
    if input_method == "⏰ Time Ranges":
        st.markdown("**Add Time Ranges:**")
        
        # Initialize session state for time ranges if not exists
        if 'temp_time_ranges' not in st.session_state:
            st.session_state.temp_time_ranges = []
        
        # Add new time range
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("Start Time", value=time(9, 0), key="start_time")
            st.caption(f"→ {start_time.strftime('%I:%M %p')}")
        with col2:
            end_time = st.time_input("End Time", value=time(17, 0), key="end_time")
            st.caption(f"→ {end_time.strftime('%I:%M %p')}")
        
        if st.button("➕ Add Time Range", use_container_width=True):
            if end_time > start_time:
                # Calculate hours
                start_dt = datetime.combine(date.today(), start_time)
                end_dt = datetime.combine(date.today(), end_time)
                duration = (end_dt - start_dt).total_seconds() / 3600
                
                st.session_state.temp_time_ranges.append({
                    "start": start_time.strftime("%I:%M %p"),
                    "end": end_time.strftime("%I:%M %p"),
                    "hours": duration
                })
                st.rerun()
            else:
                st.error("End time must be after start time")
        
        # Display current time ranges
        if st.session_state.temp_time_ranges:
            st.markdown("**Current Ranges:**")
            for idx, tr in enumerate(st.session_state.temp_time_ranges):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"{format_time_12hr(tr['start'])} - {format_time_12hr(tr['end'])} ({tr['hours']:.1f}h)")
                with col2:
                    if st.button("✖", key=f"remove_{idx}", help="Remove"):
                        st.session_state.temp_time_ranges.pop(idx)
                        st.rerun()
            
            total_hours = sum(tr['hours'] for tr in st.session_state.temp_time_ranges)
            st.success(f"**Total: {total_hours:.1f} hours**")
            time_ranges = st.session_state.temp_time_ranges.copy()
        else:
            st.info("Add your first time range above")
        
        hours = total_hours
    else:
        hours = st.number_input("Hours Worked", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
    
    project = st.text_input("Project/Task Name", placeholder="e.g., Client Meeting")
    description = st.text_area("Description", placeholder="What did you work on?")
    
    if st.button("💾 Save Entry", type="primary", use_container_width=True):
        if description and hours > 0:
            add_log(log_date, hours, description, project, time_ranges if time_ranges else None)
            st.session_state.temp_time_ranges = []  # Clear temp ranges
            st.success("✅ Entry added successfully!")
            st.rerun()
        elif hours == 0:
            st.error("Please add at least one time range or enter hours")
        else:
            st.error("Please add a description")

# Main content area
tab1, tab2, tab3 = st.tabs(["📊 Overview", "📅 All Entries", "📈 Analytics"])

with tab1:
    st.header("Summary")
    
    df = get_logs_df()
    
    if not df.empty:
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From", value=df['date'].min().date())
        with col2:
            end_date = st.date_input("To", value=df['date'].max().date())
        
        # Filter data
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        filtered_df = df[mask]
        
        if not filtered_df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_hours = filtered_df['hours'].sum()
            avg_hours = filtered_df['hours'].mean()
            total_days = filtered_df['date'].nunique()
            total_entries = len(filtered_df)
            
            col1.metric("Total Hours", f"{total_hours:.1f}h")
            col2.metric("Average Hours/Day", f"{avg_hours:.1f}h")
            col3.metric("Days Logged", total_days)
            col4.metric("Total Entries", total_entries)
            
            st.divider()
            
            # Recent entries
            st.subheader("Recent Entries")
            recent = filtered_df.head(10)[['date', 'hours', 'project', 'description']]
            recent['date'] = recent['date'].dt.strftime('%Y-%m-%d')
            st.dataframe(recent, use_container_width=True, hide_index=True)
        else:
            st.info("No entries found in the selected date range")
    else:
        st.info("👈 Start by adding your first time entry using the form on the left")

with tab2:
    st.header("All Time Entries")
    
    df = get_logs_df()
    
    if not df.empty:
        # Search and filter options
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Search", placeholder="Search in projects or descriptions...")
        with col2:
            sort_order = st.selectbox("Sort", ["Newest First", "Oldest First"])
        
        # Apply search filter
        if search:
            mask = (df['project'].str.contains(search, case=False, na=False) | 
                   df['description'].str.contains(search, case=False, na=False))
            df = df[mask]
        
        # Apply sort
        if sort_order == "Oldest First":
            df = df.sort_values('date', ascending=True)
        
        if not df.empty:
            st.write(f"**{len(df)} entries found**")
            
            # Display entries with delete option
            for idx, row in df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{row['date'].strftime('%Y-%m-%d')}** - {row['project'] if row['project'] else 'No Project'}")
                        st.caption(row['description'])
                        # Show time ranges if available
                        if 'time_ranges' in row and row['time_ranges']:
                            time_ranges_text = " | ".join([f"{format_time_12hr(tr['start'])}-{format_time_12hr(tr['end'])}" for tr in row['time_ranges']])
                            st.caption(f"⏰ {time_ranges_text}")
                    
                    with col2:
                        st.metric("Hours", f"{row['hours']:.1f}h")
                    
                    with col3:
                        # Find the actual index in the logs list
                        log_index = next(i for i, log in enumerate(st.session_state.logs) 
                                       if log['timestamp'] == row['timestamp'])
                        if st.button("🗑️", key=f"del_{log_index}", help="Delete entry"):
                            delete_log(log_index)
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No entries found matching your search")
    else:
        st.info("No entries yet. Add your first entry using the sidebar!")

with tab3:
    st.header("Analytics")
    
    df = get_logs_df()
    
    if not df.empty:
        # Hours by day
        st.subheader("Hours by Day")
        daily_hours = df.groupby(df['date'].dt.date)['hours'].sum().reset_index()
        daily_hours.columns = ['Date', 'Hours']
        st.bar_chart(daily_hours.set_index('Date'))
        
        st.divider()
        
        # Hours by project
        if df['project'].notna().any() and df['project'].str.strip().any():
            st.subheader("Hours by Project")
            project_hours = df[df['project'].str.strip() != ''].groupby('project')['hours'].sum().sort_values(ascending=False)
            st.bar_chart(project_hours)
        
        st.divider()
        
        # Weekly summary
        st.subheader("Weekly Summary")
        df['week'] = df['date'].dt.to_period('W').astype(str)
        weekly = df.groupby('week')['hours'].agg(['sum', 'mean', 'count']).reset_index()
        weekly.columns = ['Week', 'Total Hours', 'Avg Hours/Day', 'Days Worked']
        weekly['Total Hours'] = weekly['Total Hours'].round(1)
        weekly['Avg Hours/Day'] = weekly['Avg Hours/Day'].round(1)
        st.dataframe(weekly, use_container_width=True, hide_index=True)
    else:
        st.info("Add some entries to see analytics")

# Footer
st.divider()
st.caption("💡 Tip: You can export your data by copying from the 'All Entries' tab")
