import streamlit as st
import pandas as pd
import time
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import json
import base64
from io import BytesIO
import random
# Set page config
st.set_page_config(
    page_title="Web Scraping Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.session_state.dark_mode = False

# Custom CSS with dynamic theming
def get_custom_css():
    if st.session_state.dark_mode:
        bg_color = "#FFFFFF"
        card_bg = "rgba(0, 0, 0, 0.05)"
        text_color = "#000000"
    else:
        bg_color = "#FFFFFF"
        card_bg = "rgba(0, 0, 0, 0.05)"
        text_color = "#000000"
    
    return f"""
        <style>
            /* Main container */
            .main {{
                background-color: {bg_color};
                color: {text_color};
            }}
            
            /* Custom card styling */
            .stCard {{
                background-color: {card_bg};
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
            }}
            
            /* Button styling */
            .stButton>button {{
                background-color: #8b5cf6;
                color: white;
                border-radius: 20px;
                padding: 10px 25px;
                border: none;
                transition: all 0.3s ease;
                
            }}
            
            .stButton>button:hover {{
                background-color: #7c3aed;
                transform: translateY(-2px);
            }}
            
            /* Progress bar */
            .stProgress > div > div > div {{
                background-color: #8b5cf6;
            }}
            
            /* Remove watermark */
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            
            /* Custom header */
            .custom-header {{
                padding: 1rem;
                background-color: {card_bg};
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            
            /* Status indicators */
            .status-indicator {{
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
            }}
            
            .status-success {{
                background-color: #10B981;
            }}
            
            .status-warning {{
                background-color: #F59E0B;
            }}
            
            .status-error {{
                background-color: #EF4444;
            }}

            .stDeployButton{{
                display:none;
            }}
        </style>
    """

# Render custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Initialize session state variables
if 'urls' not in st.session_state:
    st.session_state.urls = []
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'results' not in st.session_state:
    st.session_state.results = []
if 'total_urls' not in st.session_state:
    st.session_state.total_urls = 10
if 'completed_urls' not in st.session_state:
    st.session_state.completed_urls = 7
if 'error_count' not in st.session_state:
    st.session_state.error_count = 0
if 'scraping_history' not in st.session_state:
    st.session_state.scraping_history = []

# Header with dark mode toggle
col1, col2, col3 = st.columns([1, 3, 1])
with col1:
   pass
with col2:
    st.title("Web Scraping Dashboard")
with col3:
    st.write("")  # Empty column for spacing

# Sidebar
with st.sidebar:
    st.title("Navigation")
    selected = st.radio(
        "",
        ["Home", "Completed", "Pending", "Files", "Log Files", "Settings"],
        key="nav"
    )
    
    # Enhanced statistics in sidebar
    st.markdown("---")
    st.subheader("Real-time Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total URLs", st.session_state.total_urls)
        st.metric("Success Rate", f"{(st.session_state.completed_urls/st.session_state.total_urls)*100:.1f}%")
    with col2:
        st.metric("Completed", st.session_state.completed_urls)
        st.metric("Errors", st.session_state.error_count)

# Main content
if selected == "Home":
    # Advanced URL input section
    st.markdown("### Add URLs")
    tab1, tab2, tab3 = st.tabs(["Upload Files", "Manual Entry", "Bulk Input"])
    
    with tab1:
        uploaded_file = st.file_uploader("Upload URL list (TXT/CSV)", type=['txt', 'csv'])
        if uploaded_file:
            try:
                if uploaded_file.type == "text/csv":
                    df = pd.read_csv(uploaded_file)
                    urls = df.iloc[:, 0].tolist()
                else:
                    content = uploaded_file.read().decode()
                    urls = content.split('\n')
                st.session_state.urls.extend([url.strip() for url in urls if url.strip()])
                st.success(f"Successfully added {len(urls)} URLs")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

    with tab2:
        url_input = st.text_input("Enter URL")
        col1, col2 = st.columns([3, 1])
        
        
        if st.button("Add URL"):
            if url_input:
                st.session_state.urls.append(url_input)
                st.success(f"Added URL: {url_input}")
            

    with tab3:
        bulk_urls = st.text_area("Enter multiple URLs (one per line)")
        if st.button("Add Bulk URLs"):
            urls = bulk_urls.split('\n')
            st.session_state.urls.extend([url.strip() for url in urls if url.strip()])
            st.success(f"Added {len(urls)} URLs")

    # Scraping Configuration
    st.markdown("### Scraping Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="stCard">
            <h4>Basic Settings</h4>
        """, unsafe_allow_html=True)
        delay = st.slider("Delay between requests (seconds)", 0, 10, 2)
        timeout = st.slider("Request timeout (seconds)", 1, 30, 10)
        max_retries = st.slider("Max retries per URL", 0, 5, 3)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="stCard">
            <h4>Advanced Settings</h4>
        """, unsafe_allow_html=True)
        
        headers = st.text_area("Custom Headers (JSON)", "{\"User-Agent\": \"Mozilla/5.0\"}")
        st.markdown("</div>", unsafe_allow_html=True)

    # Progress and Status
    st.markdown("### Current Progress")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="stCard">
            <h4>Scraping Status</h4>
        """, unsafe_allow_html=True)
        st.progress(st.session_state.completed_urls/st.session_state.total_urls)
        
        # Enhanced status display
        st.markdown("#### Status Overview")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
                <div class="status-indicator status-success"></div> Success: {}
                <br>
                <div class="status-indicator status-warning"></div> Pending: {}
                <br>
                <div class="status-indicator status-error"></div> Failed: {}
            """.format(
                st.session_state.completed_urls,
                st.session_state.total_urls - st.session_state.completed_urls - st.session_state.error_count,
                st.session_state.error_count
            ), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # Enhanced visualization
        data = pd.DataFrame({
            'Category': ['Success', 'Pending', 'Failed'],
            'Count': [
                st.session_state.completed_urls,
                st.session_state.total_urls - st.session_state.completed_urls - st.session_state.error_count,
                st.session_state.error_count
            ]
        })
        
        fig = px.pie(data, values='Count', names='Category',
                    color_discrete_map={'Success':'#10B981',
                                      'Pending':'#F59E0B',
                                      'Failed':'#EF4444'})
        fig.update_layout(
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)

    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start Scraping", key="start"):
            with st.spinner('Scraping in progress...'):
                # Simulate scraping progress
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.05)
                    progress_bar.progress(i + 1)
                st.success('Scraping completed!')
                
    with col2:
        if st.button("Pause", key="pause"):
            st.info("Scraping paused")
            
    with col3:
        if st.button("Stop", key="stop"):
            st.warning("Scraping stopped")

elif selected == "Completed":
    st.markdown("### Completed Jobs")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        date_filter = st.date_input("Filter by date")
    with col2:
        status_filter = st.multiselect("Filter by status", ["Success", "Failed"])
    with col3:
        search = st.text_input("Search URLs")
    
    # Sample completed jobs data with more details
    completed_data = pd.DataFrame({
        'URL': ['https://example1.com', 'https://example2.com'],
        'Results': [120, 85],
        'Duration': ['2m 30s', '1m 45s'],
        'Status': ['Success', 'Failed'],
        'Timestamp': ['2024-02-23 14:30', '2024-02-23 14:35'],
        'Data Size': ['1.2 MB', '0.8 MB']
    })
    
    # Add interactive elements to the table
    st.dataframe(completed_data, use_container_width=True)
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download Results",
            data=completed_data.to_csv(index=False),
            file_name="completed_jobs.csv",
            mime="text/csv"
        )
    with col2:
        st.button("Clear History")

elif selected == "Pending":
    st.markdown("### Pending Jobs")
    
    # Queue management
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Queue Settings")
        max_concurrent = st.slider("Max concurrent jobs", 1, 10, 3)
        priority = st.selectbox("Default priority", ["High", "Medium", "Low"])
    
    with col2:
        st.markdown("#### Queue Status")
        st.metric("Jobs in queue", st.session_state.total_urls - st.session_state.completed_urls)
        st.metric("Estimated time remaining", "1h 30m")
    
    # Pending jobs table with controls
    pending_data = pd.DataFrame({
        'URL': ['https://example3.com', 'https://example4.com'],
        'Status': ['Queued', 'Processing'],
        'Priority': ['High', 'Medium'],
        'Added': ['5 mins ago', '2 mins ago'],
        'Actions': ['Cancel', 'Pause']
    })
    st.dataframe(pending_data, use_container_width=True)

elif selected == "Files":
    st.markdown("### File Management")
    
    # File statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", "156")
    with col2:
        st.metric("Total Size", "2.3 GB")
    with col3:
        st.metric("Average File Size", "15 MB")
    
    # File browser
    st.markdown("#### Saved Files")
    file_list = pd.DataFrame({
        'Filename': ['results_20240223.csv', 'data_export.json'],
        'Size': ['1.2 MB', '0.8 MB'],
        'Created': ['2024-02-23 14:30', '2024-02-23 14:35'],
        'Type': ['CSV', 'JSON']
    })
    st.dataframe(file_list, use_container_width=True)
    
    


elif selected == "Log Files":
    st.markdown("### System Logs")
    
    # Log filters
    col1, col2 = st.columns(2)
    with col1:
        log_level = st.multiselect("Log Level", ["INFO", "WARNING", "ERROR", "DEBUG"], default=["INFO", "WARNING", "ERROR"])
    with col2:
        date_range = st.date_input("Date Range", [datetime.now().date(), datetime.now().date()])
    
    # Search and refresh
    col3, col4 = st.columns([3, 1])
    with col3:
        log_search = st.text_input("Search logs...")
    with col4:
        st.button("🔄 Refresh")
    
    # Log viewer
    st.markdown("#### Live Log Feed")
    log_data = pd.DataFrame({
        'Timestamp': ['2024-02-23 14:30:00', '2024-02-23 14:30:05', '2024-02-23 14:30:10'],
        'Level': ['INFO', 'WARNING', 'ERROR'],
        'Component': ['Scraper', 'Rate Limiter', 'Parser'],
        'Message': [
            'Started scraping https://example1.com',
            'Rate limit detected, waiting for 60 seconds...',
            'Failed to parse content: Invalid HTML structure'
        ]
    })
    
    # Color-coded log display
    def color_log_level(val):
        colors = {
            'INFO': '#10B981',
            'WARNING': '#F59E0B',
            'ERROR': '#EF4444',
            'DEBUG': '#6B7280'
        }
        return f'color: {colors.get(val, "white")}'
    
    styled_logs = log_data.style.apply(lambda x: pd.Series(x.map(lambda v: color_log_level(v) if v in ['INFO', 'WARNING', 'ERROR', 'DEBUG'] else ''), index=x.index), axis=0)
    st.dataframe(styled_logs, use_container_width=True)
    
    # Log analysis
    st.markdown("#### Log Analysis")
    col1, col2 = st.columns(2)
    with col1:
        # Error distribution pie chart
        error_data = pd.DataFrame({
            'Error Type': ['Rate Limit', 'Parser Error', 'Network Timeout', 'Other'],
            'Count': [15, 8, 5, 3]
        })
        fig = px.pie(error_data, values='Count', names='Error Type',
                    title='Error Distribution')
        fig.update_layout(showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    
    
    # Log management
    st.markdown("#### Log Management")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Download Logs"):
            # Create download link for logs
            download_link=''
            tmp_download_link = download_link(log_data, 'system_logs.csv', 'Click here to download')
            st.markdown(tmp_download_link, unsafe_allow_html=True)
    with col2:
        if st.button("Clear Logs"):
            st.warning("This will clear all logs. Are you sure?")
    

elif selected == "Settings":
    st.markdown("### System Settings")
    
    # General Settings
    st.markdown("#### General Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="stCard">
            <h4>Display Settings</h4>
        """, unsafe_allow_html=True)
        
        st.selectbox("Date format", ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"])
        st.number_input("Items per page", min_value=10, max_value=100, value=25)
        st.markdown("</div>", unsafe_allow_html=True)
    
   
    
    # Scraping Settings
    st.markdown("#### Scraping Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="stCard">
            <h4>Performance Settings</h4>
        """, unsafe_allow_html=True)
        st.slider("Max concurrent requests", 1, 20, 5)
        st.slider("Request timeout (seconds)", 5, 60, 30)
        st.number_input("Max retries", min_value=0, max_value=10, value=3)
        st.markdown("</div>", unsafe_allow_html=True)
    
   
    

    
    # Storage Settings
    st.markdown("#### Storage Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="stCard">
            <h4>Data Storage</h4>
        """, unsafe_allow_html=True)
        st.selectbox("Storage type", ["Local"])
        st.text_input("Storage path")
        
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stCard">
            <h4>Export Settings</h4>
        """, unsafe_allow_html=True)
        st.multiselect("Default export formats", ["Excel"])
        
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Save Settings
    st.markdown("#### Save Changes")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Settings"):
            st.success("Settings saved successfully!")
    with col2:
        if st.button("Reset to Defaults"):
            st.warning("This will reset all settings to default values. Are you sure?")

# Helper function for creating download links
def download_link(df, filename, link_text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{link_text}</a>'
    return href
