"""
Streamlit UI for the Home Assistant Smart Alarm Clock.

This module provides a web-based user interface for managing alarms.
"""

import streamlit as st
import sys
import os
from pathlib import Path
import logging
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.config import ConfigManager
from app.database import DatabaseManager, Alarm
from app.utils import setup_logging, format_days_list, validate_alarm_data

# Setup logging
setup_logging('logs/streamlit_ui.log', 'INFO')
logger = logging.getLogger('streamlit_ui')

# Initialize configuration and database
@st.cache_resource
def init_resources():
    """Initialize configuration and database resources."""
    config = ConfigManager()
    db_path = config.get('database_path', 'alarms.db')
    db_manager = DatabaseManager(db_path)
    return config, db_manager

config, db_manager = init_resources()

# Set page configuration
st.set_page_config(
    page_title="Home Assistant Smart Alarm Clock",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .alarm-card {
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .alarm-enabled {
        background-color: rgba(0, 200, 0, 0.1);
        border-left: 5px solid rgba(0, 200, 0, 0.5);
    }
    .alarm-disabled {
        background-color: rgba(200, 0, 0, 0.1);
        border-left: 5px solid rgba(200, 0, 0, 0.5);
    }
    .sidebar-header {
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.markdown('<div class="sidebar-header">⏰ Smart Alarm Clock</div>', unsafe_allow_html=True)

# Get all alarms for sidebar
alarms = db_manager.get_all_alarms()

# Add alarm button in sidebar
if st.sidebar.button("➕ Add New Alarm"):
    st.session_state.page = "add_alarm"
    st.session_state.selected_alarm = None

# List alarms in sidebar
st.sidebar.markdown("### Alarms")
for alarm in alarms:
    status = "🟢" if alarm.enabled else "🔴"
    if st.sidebar.button(f"{status} {alarm.name} - {alarm.time}", key=f"alarm_{alarm.id}"):
        st.session_state.page = "view_alarm"
        st.session_state.selected_alarm = alarm.id

# Settings button
if st.sidebar.button("⚙️ Settings"):
    st.session_state.page = "settings"
    st.session_state.selected_alarm = None

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "dashboard"
if 'selected_alarm' not in st.session_state:
    st.session_state.selected_alarm = None

# Dashboard page
def show_dashboard():
    """Show the dashboard page with overview of alarms."""
    st.markdown('<div class="main-header">Home Assistant Smart Alarm Clock</div>', unsafe_allow_html=True)
    
    # Display upcoming alarms
    st.markdown('<div class="section-header">Upcoming Alarms</div>', unsafe_allow_html=True)
    
    enabled_alarms = [a for a in alarms if a.enabled]
    if not enabled_alarms:
        st.info("No active alarms. Click 'Add New Alarm' to create one.")
    else:
        # Sort alarms by time
        enabled_alarms.sort(key=lambda a: a.time)
        
        # Display each alarm
        for alarm in enabled_alarms:
            days = format_days_list(alarm.days_list)
            with st.container():
                st.markdown(f"""
                <div class="alarm-card alarm-enabled">
                    <h3>{alarm.name} - {alarm.time}</h3>
                    <p>Days: {days}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Display disabled alarms
    disabled_alarms = [a for a in alarms if not a.enabled]
    if disabled_alarms:
        st.markdown('<div class="section-header">Disabled Alarms</div>', unsafe_allow_html=True)
        
        # Display each alarm
        for alarm in disabled_alarms:
            days = format_days_list(alarm.days_list)
            with st.container():
                st.markdown(f"""
                <div class="alarm-card alarm-disabled">
                    <h3>{alarm.name} - {alarm.time}</h3>
                    <p>Days: {days}</p>
                </div>
                """, unsafe_allow_html=True)

# View/edit alarm page
def show_alarm_detail():
    """Show the alarm detail page for viewing and editing an alarm."""
    alarm_id = st.session_state.selected_alarm
    alarm = db_manager.get_alarm_by_id(alarm_id)
    
    if not alarm:
        st.error(f"Alarm with ID {alarm_id} not found")
        st.session_state.page = "dashboard"
        return
    
    st.markdown(f'<div class="main-header">{alarm.name}</div>', unsafe_allow_html=True)
    
    # Create tabs for view and edit
    tab1, tab2 = st.tabs(["View", "Edit"])
    
    # View tab
    with tab1:
        status = "Enabled" if alarm.enabled else "Disabled"
        status_color = "green" if alarm.enabled else "red"
        
        st.markdown(f"<h3 style='color: {status_color};'>{status}</h3>", unsafe_allow_html=True)
        st.markdown(f"**Time:** {alarm.time}")
        st.markdown(f"**Days:** {format_days_list(alarm.days_list)}")
        st.markdown(f"**Media:** {alarm.media_url} ({alarm.media_type})")
        
        with st.expander("Advanced Settings"):
            st.markdown(f"**Volume Steps:** {alarm.volume_steps_list}")
            st.markdown(f"**Volume Step Delay:** {alarm.volume_step_delay} seconds")
            st.markdown(f"**Person Entity:** {alarm.person_entity or 'None'}")
            st.markdown(f"**Created:** {alarm.created_at}")
            st.markdown(f"**Last Updated:** {alarm.updated_at}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if alarm.enabled:
                if st.button("Disable Alarm"):
                    db_manager.update_alarm(alarm_id, {"enabled": False})
                    st.success("Alarm disabled")
                    st.rerun()
            else:
                if st.button("Enable Alarm"):
                    db_manager.update_alarm(alarm_id, {"enabled": True})
                    st.success("Alarm enabled")
                    st.rerun()
        
        with col2:
            if st.button("Duplicate Alarm"):
                # Create a copy of the alarm
                new_alarm_data = alarm.to_dict()
                del new_alarm_data['id']
                del new_alarm_data['created_at']
                del new_alarm_data['updated_at']
                new_alarm_data['name'] = f"Copy of {new_alarm_data['name']}"
                
                new_alarm = db_manager.create_alarm(new_alarm_data)
                st.success(f"Created duplicate alarm: {new_alarm.name}")
                st.session_state.selected_alarm = new_alarm.id
                st.rerun()
        
        with col3:
            if st.button("Delete Alarm", type="primary", use_container_width=True):
                st.session_state.confirm_delete = True
        
        # Confirmation dialog for deletion
        if st.session_state.get('confirm_delete', False):
            st.warning("Are you sure you want to delete this alarm? This action cannot be undone.")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Cancel"):
                    st.session_state.confirm_delete = False
                    st.rerun()
            
            with col2:
                if st.button("Confirm Delete", type="primary"):
                    db_manager.delete_alarm(alarm_id)
                    st.success("Alarm deleted")
                    st.session_state.page = "dashboard"
                    st.session_state.selected_alarm = None
                    st.rerun()
    
    # Edit tab
    with tab2:
        with st.form("edit_alarm_form"):
            name = st.text_input("Alarm Name", value=alarm.name)
            time = st.text_input("Alarm Time (HH:MM)", value=alarm.time)
            
            # Days selection
            st.write("Days")
            days_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            days_values = [0, 1, 2, 3, 4, 5, 6]
            selected_days = [days_options[day] for day in alarm.days_list if day < len(days_options)]
            
            days = st.multiselect(
                "Select Days",
                options=days_options,
                default=selected_days
            )
            
            # Convert day names back to numbers
            days_list = [days_options.index(day) for day in days if day in days_options]
            
            # Media settings
            media_url = st.text_input("Media URL", value=alarm.media_url)
            media_type = st.selectbox(
                "Media Type",
                options=["music", "playlist"],
                index=0 if alarm.media_type == "music" else 1
            )
            
            # Advanced settings
            with st.expander("Advanced Settings"):
                volume_steps_str = ", ".join([str(v) for v in alarm.volume_steps_list])
                volume_steps = st.text_input(
                    "Volume Steps (comma-separated values between 0.0 and 1.0)",
                    value=volume_steps_str
                )
                
                volume_step_delay = st.number_input(
                    "Volume Step Delay (seconds)",
                    min_value=1,
                    max_value=60,
                    value=alarm.volume_step_delay
                )
                
                person_entity = st.text_input(
                    "Person Entity (for presence detection)",
                    value=alarm.person_entity or ""
                )
                
                enabled = st.checkbox("Enabled", value=alarm.enabled)
            
            # Submit button
            submitted = st.form_submit_button("Save Changes")
            
            if submitted:
                # Process volume steps
                try:
                    volume_steps_list = [float(v.strip()) for v in volume_steps.split(",")]
                    # Validate volume steps
                    if not all(0 <= v <= 1 for v in volume_steps_list):
                        st.error("Volume steps must be between 0.0 and 1.0")
                        return
                except ValueError:
                    st.error("Invalid volume steps format. Use comma-separated decimal values.")
                    return
                
                # Create update data
                update_data = {
                    "name": name,
                    "time": time,
                    "days": days_list,
                    "media_url": media_url,
                    "media_type": media_type,
                    "volume_steps": volume_steps_list,
                    "volume_step_delay": volume_step_delay,
                    "person_entity": person_entity if person_entity else None,
                    "enabled": enabled
                }
                
                # Validate update data
                errors = validate_alarm_data(update_data)
                if errors:
                    for field, error in errors.items():
                        st.error(f"{field}: {error}")
                    return
                
                # Update alarm
                updated_alarm = db_manager.update_alarm(alarm_id, update_data)
                if updated_alarm:
                    st.success("Alarm updated successfully")
                    st.rerun()
                else:
                    st.error("Failed to update alarm")

# Add alarm page
def show_add_alarm():
    """Show the add alarm page for creating a new alarm."""
    st.markdown('<div class="main-header">Add New Alarm</div>', unsafe_allow_html=True)
    
    with st.form("add_alarm_form"):
        name = st.text_input("Alarm Name", value="New Alarm")
        time = st.text_input("Alarm Time (HH:MM)", value="07:00")
        
        # Days selection
        st.write("Days")
        days_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days_values = [0, 1, 2, 3, 4, 5, 6]
        
        # Default to weekdays
        default_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        days = st.multiselect(
            "Select Days",
            options=days_options,
            default=default_days
        )
        
        # Convert day names to numbers
        days_list = [days_options.index(day) for day in days if day in days_options]
        
        # Media settings
        media_url = st.text_input("Media URL", value="/media/audio/wake_up.mp3")
        media_type = st.selectbox(
            "Media Type",
            options=["music", "playlist"],
            index=0
        )
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            volume_steps = st.text_input(
                "Volume Steps (comma-separated values between 0.0 and 1.0)",
                value="0.2, 0.3, 0.4, 0.5, 0.6, 0.7"
            )
            
            volume_step_delay = st.number_input(
                "Volume Step Delay (seconds)",
                min_value=1,
                max_value=60,
                value=20
            )
            
            person_entity = st.text_input(
                "Person Entity (for presence detection)",
                value="person.user"
            )
            
            enabled = st.checkbox("Enabled", value=True)
        
        # Submit button
        submitted = st.form_submit_button("Create Alarm")
        
        if submitted:
            # Process volume steps
            try:
                volume_steps_list = [float(v.strip()) for v in volume_steps.split(",")]
                # Validate volume steps
                if not all(0 <= v <= 1 for v in volume_steps_list):
                    st.error("Volume steps must be between 0.0 and 1.0")
                    return
            except ValueError:
                st.error("Invalid volume steps format. Use comma-separated decimal values.")
                return
            
            # Create alarm data
            alarm_data = {
                "name": name,
                "time": time,
                "days": days_list,
                "media_url": media_url,
                "media_type": media_type,
                "volume_steps": volume_steps_list,
                "volume_step_delay": volume_step_delay,
                "person_entity": person_entity if person_entity else None,
                "enabled": enabled
            }
            
            # Validate alarm data
            errors = validate_alarm_data(alarm_data)
            if errors:
                for field, error in errors.items():
                    st.error(f"{field}: {error}")
                return
            
            # Create alarm
            alarm = db_manager.create_alarm(alarm_data)
            if alarm:
                st.success(f"Alarm '{alarm.name}' created successfully")
                st.session_state.page = "view_alarm"
                st.session_state.selected_alarm = alarm.id
                st.rerun()
            else:
                st.error("Failed to create alarm")

# Settings page
def show_settings():
    """Show the settings page for configuring the application."""
    st.markdown('<div class="main-header">Settings</div>', unsafe_allow_html=True)
    
    # Home Assistant settings
    st.markdown('<div class="section-header">Home Assistant Connection</div>', unsafe_allow_html=True)
    
    with st.form("ha_settings_form"):
        ha_url = st.text_input("Home Assistant URL", value=config.get("ha_url"))
        ha_token = st.text_input("Long-Lived Access Token", value=config.get("ha_token"), type="password")
        voice_pe_entity = st.text_input("Media Player Entity", value=config.get("voice_pe_entity"))
        
        submitted = st.form_submit_button("Save Home Assistant Settings")
        
        if submitted:
            config.set("ha_url", ha_url)
            config.set("ha_token", ha_token)
            config.set("voice_pe_entity", voice_pe_entity)
            config.save("config.yaml")
            st.success("Home Assistant settings saved")
    
    # Notification settings
    st.markdown('<div class="section-header">Notifications</div>', unsafe_allow_html=True)
    
    with st.form("notification_settings_form"):
        gotify_url = st.text_input("Gotify URL", value=config.get("gotify_url", ""))
        gotify_token = st.text_input("Gotify Token", value=config.get("gotify_token", ""), type="password")
        
        submitted = st.form_submit_button("Save Notification Settings")
        
        if submitted:
            config.set("gotify_url", gotify_url)
            config.set("gotify_token", gotify_token)
            config.save("config.yaml")
            st.success("Notification settings saved")
    
    # System settings
    st.markdown('<div class="section-header">System Settings</div>', unsafe_allow_html=True)
    
    with st.form("system_settings_form"):
        timezone = st.text_input("Timezone", value=config.get("timezone"))
        log_level = st.selectbox(
            "Log Level",
            options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=1  # Default to INFO
        )
        health_check_port = st.number_input(
            "Health Check Port",
            min_value=1024,
            max_value=65535,
            value=int(config.get("health_check_port", 8080))
        )
        
        submitted = st.form_submit_button("Save System Settings")
        
        if submitted:
            config.set("timezone", timezone)
            config.set("log_level", log_level)
            config.set("health_check_port", health_check_port)
            config.save("config.yaml")
            st.success("System settings saved")
    
    # Database operations
    st.markdown('<div class="section-header">Database Operations</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Alarms"):
            import json
            from datetime import datetime
            
            alarms = db_manager.get_all_alarms()
            export_data = [alarm.to_dict() for alarm in alarms]
            
            # Create export file
            export_file = f"alarm_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, "w") as f:
                json.dump(export_data, f, indent=2)
            
            st.success(f"Exported {len(alarms)} alarms to {export_file}")
            
            # Provide download link
            with open(export_file, "r") as f:
                st.download_button(
                    label="Download Export File",
                    data=f,
                    file_name=export_file,
                    mime="application/json"
                )
    
    with col2:
        uploaded_file = st.file_uploader("Import Alarms", type=["json"])
        if uploaded_file is not None:
            import json
            
            try:
                import_data = json.load(uploaded_file)
                
                if not isinstance(import_data, list):
                    st.error("Invalid import file format. Expected a list of alarms.")
                    return
                
                imported_count = 0
                for alarm_data in import_data:
                    # Remove ID and timestamps
                    if "id" in alarm_data:
                        del alarm_data["id"]
                    if "created_at" in alarm_data:
                        del alarm_data["created_at"]
                    if "updated_at" in alarm_data:
                        del alarm_data["updated_at"]
                    
                    # Validate alarm data
                    errors = validate_alarm_data(alarm_data)
                    if not errors:
                        db_manager.create_alarm(alarm_data)
                        imported_count += 1
                
                st.success(f"Imported {imported_count} alarms successfully")
                st.rerun()
            except Exception as e:
                st.error(f"Error importing alarms: {str(e)}")

# Route to the appropriate page
if st.session_state.page == "dashboard":
    show_dashboard()
elif st.session_state.page == "view_alarm":
    show_alarm_detail()
elif st.session_state.page == "add_alarm":
    show_add_alarm()
elif st.session_state.page == "settings":
    show_settings()
else:
    show_dashboard()

# Footer
st.markdown("---")
st.markdown("Home Assistant Smart Alarm Clock | v0.3.0")
