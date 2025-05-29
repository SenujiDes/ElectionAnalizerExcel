# Mannar District Election Results Analyzer
import streamlit as st  # Import Streamlit for building the web app UI
import pandas as pd     # Import pandas for data manipulation
import plotly.express as px       # Import Plotly Express for simple plotting
import plotly.graph_objects as go  # Import Plotly Graph Objects for advanced plots
from plotly.subplots import make_subplots  # For creating complex subplot layouts


def parse_election_data(df):
    """Parse the election data from the specific format shown"""
    councils_data = {}  # Dictionary to hold processed DataFrames for each council
    
    # Convert all data to string type to simplify pattern matching
    df_str = df.astype(str)
    
    # List to record where each council section starts and its name
    council_sections = []
    
    # Iterate over each row to find council section headers
    for idx, row in df_str.iterrows():
        for col in df_str.columns:
            cell_value = str(row[col]).strip()  # Get cell value as stripped string
            # Check if the cell indicates a council section (like "1 - XYZ COUNCIL")

            prefixes = tuple(f"{i} -" for i in range(1, 24))
            text = cell_value.strip().lower()
                        
            if (cell_value.startswith(('1 -', '2 -', '3 -', '4 -', '5 -', '6 -', '7 -', '8 -', '9 -', '10 -','11 -' ,'12 -','13 -','14 -','15 -','16 -','17 -','18 -','19 -','20 -','21 -','22 -','23 -' )) and 
                text.startswith(prefixes) and ("council" in text or "sabha" in text)):
                council_sections.append((idx, cell_value))  # Save the row index and council title
                break  # Stop checking other columns in this row once found
    
    # Debug output: how many sections and their names
    st.write(f"Found {len(council_sections)} council sections: {[section[1] for section in council_sections]}")
    
    # Process each detected council section
    for i, (start_idx, council_name) in enumerate(council_sections):
        try:
            # Determine where this section ends (right before the next section or end of data)
            if i < len(council_sections) - 1:
                end_idx = council_sections[i + 1][0]
            else:
                end_idx = len(df_str)
            
            section_data = []    # Temporary list for storing rows of this section
            header_found = False  # Flag to mark when the column header row is detected
            
            # Loop through rows belonging to this section
            for row_idx in range(start_idx, end_idx):
                row = df_str.iloc[row_idx]  # Get the row as a Series
                
                # Skip the title row itself
                if row_idx == start_idx:
                    continue
                
                # Look for the row that contains the header labels "Party", "Votes", "Total"
                if not header_found:
                    row_str = ' '.join(row.values).upper()
                    if 'PARTY' in row_str and 'VOTES' in row_str and 'TOTAL' in row_str:
                        header_found = True
                        continue  # Skip the header row and begin collecting data next
                
                # Once header is found, collect rows of party data
                if header_found:
                    # Filter out empty or invalid cells
                    row_data = [cell for cell in row.values if cell not in ['nan', '', None]]
                    # Expect at least three values: Party, Votes, Seats (Total)
                    if len(row_data) >= 3:
                        party = row_data[0]  # Political party name
                        try:
                            # Convert vote and seat counts to integers, handling missing data
                            votes = int(float(row_data[1])) if row_data[1] != 'nan' else 0
                            seats = int(float(row_data[2])) if row_data[2] != 'nan' else 0
                            
                            # Skip any "Total" summary rows
                            if party.upper() != 'TOTAL':
                                section_data.append({
                                    'Party': party,
                                    'Votes': votes,
                                    'Seats': seats
                                })
                        except (ValueError, IndexError):
                            # Skip rows that can't be parsed
                            continue
            
            # After collecting raw rows, create a DataFrame
            if section_data:
                # create an in-memory table (DataFrame) from Python data structures
                council_df = pd.DataFrame(section_data)
                # Remove parties with zero votes to clean up the view
                council_df = council_df[council_df['Votes'] > 0]
                councils_data[council_name] = council_df  # Store the cleaned DataFrame
                
        except Exception as e:
            # Display an error message if processing fails for a council
            st.error(f"Error processing {council_name}: {str(e)}")
            continue
    
    return councils_data  # Return dictionary of all councils' data


def create_council_summary_and_charts(council_name, df):
    """Create summary metrics and charts for a single council"""
    st.markdown("---")  # Separator line
    st.markdown(f"## 🏛️ {council_name}")  # Council title
    
    # Create four columns for summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_votes = df['Votes'].sum()    # Sum of all votes in this council
    total_seats = df['Seats'].sum()    # Sum of all seats won
    num_parties = len(df)              # Number of parties contested
    winner = df.loc[df['Votes'].idxmax(), 'Party']  # Party with maximum votes
    
    # Display summary metrics in the UI
    with col1:
        st.metric("📊 Total Votes", f"{total_votes:,}")
    with col2:
        st.metric("🪑 Total Seats", f"{total_seats}")
    with col3:
        st.metric("🏃 Parties Contested", f"{num_parties}")
    with col4:
        # Truncate long party names for display
        st.metric("🏆 Most Votes", winner[:15] + "..." if len(winner) > 15 else winner)
    
    # Expandable section to view detailed table
    with st.expander(f"📋 View Detailed Results - {council_name}", expanded=False):
        display_df = df.copy()
        # Calculate percentage share of votes and seats
        display_df['Vote %'] = (display_df['Votes'] / total_votes * 100).round(2)
        display_df['Seat %'] = (display_df['Seats'] / total_seats * 100).round(2) if total_seats > 0 else 0
        st.dataframe(display_df, use_container_width=True)
    
    # Create two side-by-side charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗳️ Vote Share Distribution")
        # Pie chart of vote shares
        fig_pie = px.pie(
            df,
            values='Votes',
            names='Party',
            title="Vote Distribution",
            height=400
        )
        fig_pie.update_traces(
            textposition='inside', 
            textinfo='percent',
            hovertemplate='<b>%{label}</b><br>Votes: %{value:,}<br>Percentage: %{percent}<extra></extra>'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("🏛️ Seats Distribution")
        seats_df = df[df['Seats'] > 0]  # Only show parties that won seats
        if not seats_df.empty:
            # Bar chart of seats won
            fig_bar = px.bar(
                seats_df,
                x='Party',
                y='Seats',
                title="Seats Won by Party",
                height=400,
                color='Seats',
                color_continuous_scale="viridis",
                text='Seats'
            )
            fig_bar.update_traces(textposition='outside')
            fig_bar.update_xaxes(tickangle=45)
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No seats data available")
    
    # Combined bar + line chart: votes vs seats
    st.subheader("📈 Performance Analysis: Votes vs Seats")
    fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])
    df_sorted = df.sort_values('Votes', ascending=True)  # Sort for clearer visualization
    
    # Add bar trace for votes
    fig.add_trace(
        go.Bar(
            x=df_sorted['Party'],
            y=df_sorted['Votes'],
            name="Votes Received",
            marker_color="lightblue",
            opacity=0.8,
            text=df_sorted['Votes'],
            textposition='outside'
        ),
        secondary_y=False,
    )
    
    # Add line trace for seats
    fig.add_trace(
        go.Scatter(
            x=df_sorted['Party'],
            y=df_sorted['Seats'],
            mode="lines+markers+text",
            name="Seats Won",
            line=dict(color="red", width=3),
            marker=dict(size=10, color="red"),
            text=df_sorted['Seats'],
            textposition="top center"
        ),
        secondary_y=True,
    )
    
    # Configure axes titles
    fig.update_xaxes(title_text="Political Parties", tickangle=45)
    fig.update_yaxes(title_text="Number of Votes", secondary_y=False)
    fig.update_yaxes(title_text="Number of Seats", secondary_y=True)
    fig.update_layout(
        height=500,
        hovermode='x unified',
        title=f"Vote-Seat Conversion - {council_name.split(' - ')[1] if ' - ' in council_name else council_name}"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # # Key insights section: vote efficiency calculation
    # st.subheader("🔍 Key Insights")
    # df_with_efficiency = df.copy()
    # df_with_efficiency['Vote_Efficiency'] = df_with_efficiency['Seats'] / df_with_efficiency['Votes'] * 1000

    # most_efficient = df_with_efficiency.loc[df_with_efficiency['Vote_Efficiency'].idxmax()]
    # least_efficient = None
    # if len(df_with_efficiency[df_with_efficiency['Seats'] > 0]) > 0:
    #     least_efficient = df_with_efficiency[df_with_efficiency['Seats'] > 0].loc[
    #         df_with_efficiency[df_with_efficiency['Seats'] > 0]['Vote_Efficiency'].idxmin()
    #     ]
    
    # insight_col1, insight_col2 = st.columns(2)
    
    # with insight_col1:
    #     st.info(f"🎯 **Most Vote-Efficient Party**: {most_efficient['Party']} - {most_efficient['Vote_Efficiency']:.2f} seats per 1000 votes")
    # with insight_col2:
    #     if least_efficient is not None:
    #         st.info(f"📉 **Least Vote-Efficient Party**: {least_efficient['Party']} - {least_efficient['Vote_Efficiency']:.2f} seats per 1000 votes")
    st.subheader("🔍 Key Insights")
    
    # Find most voted and most seated parties
    most_voted_party = df.loc[df['Votes'].idxmax()]
    most_seated_party = df.loc[df['Seats'].idxmax()]
    
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        st.info(f"🗳️ **Most Voted Party**: {most_voted_party['Party']} - {most_voted_party['Votes']:,} votes ({(most_voted_party['Votes']/total_votes*100):.1f}%)")
    
    with insight_col2:
        st.info(f"🏆 **Most Seated Party**: {most_seated_party['Party']} - {most_seated_party['Seats']} seats ({(most_seated_party['Seats']/total_seats*100):.1f}%)")

def main():
    st.set_page_config(
        page_title="Election Results Analyzer",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🗳️ Election Results Analyzer")
    st.markdown("**Comprehensive analysis of Municipal Council and Pradeshiya Sabha elections**")
    
    uploaded_file = st.file_uploader(
        "📂 Upload Election Results Excel File",
        type=["xlsx", "xls"],
        help="Upload the Excel file containing election results for Mannar district councils"
    )
    
    if uploaded_file:
        try:
            # Read the Excel file
            df = pd.read_excel(uploaded_file)
            
            st.success("✅ File uploaded successfully!")
            
            # Show file info
            with st.expander("📄 File Information", expanded=False):
                st.write(f"**Rows**: {len(df)}")
                st.write(f"**Columns**: {len(df.columns)}")
                st.dataframe(df.head(10))
            
            # Parse the election data
            with st.spinner("🔄 Parsing election data..."):
                councils_data = parse_election_data(df)
            
            if councils_data:
                st.success(f"✅ Successfully parsed {len(councils_data)} council(s)")
                
                # Sidebar for navigation
                st.sidebar.title("📋 Council Navigation")
                selected_council = st.sidebar.selectbox(
                    "Select a council to view:",
                    options=list(councils_data.keys()),
                    index=0
                )
                
                # Show overview
                st.markdown("## 📊 Overview")
                
                if len(councils_data) <= 5:
                    # Show in columns for 5 or fewer councils
                    overview_cols = st.columns(len(councils_data))
                    
                    for i, (council_name, council_df) in enumerate(councils_data.items()):
                        with overview_cols[i]:
                            st.metric(
                                label=council_name.split(' - ')[1] if ' - ' in council_name else council_name,
                                value=f"{council_df['Votes'].sum():,} votes",
                                delta=f"{council_df['Seats'].sum()} seats"
                            )
                else:
                    # Show in attractive grid layout for more than 5 councils
                    show_all_overview = st.checkbox("Show all councils in overview", value=False)
                    
                    # Create a grid with 3 columns
                    councils_list = list(councils_data.items())
                    rows = (len(councils_list) + 2) // 3  # Calculate number of rows needed
                    
                    # Show only first row if show_all_overview is False
                    display_rows = rows if show_all_overview else 1
                    
                    for row in range(display_rows):
                        cols = st.columns(3)
                        for col_idx in range(3):
                            council_idx = row * 3 + col_idx
                            if council_idx < len(councils_list):
                                council_name, council_df = councils_list[council_idx]
                                with cols[col_idx]:
                                    # Create attractive metric cards
                                    total_votes = council_df['Votes'].sum()
                                    total_seats = council_df['Seats'].sum()
                                    winner = council_df.loc[council_df['Votes'].idxmax(), 'Party']
                                    
                                    # Shortened council name for display
                                    display_name = council_name.split(' - ')[1] if ' - ' in council_name else council_name
                                    display_name = display_name.replace('MANNAR ', '').replace('PRADESHIYA SABHA', 'P.S.')
                                    
                                    st.markdown(f"""
                                    <div style="background: rgba(0, 0, 0, 0.8); border: 1px solid rgba(255, 255, 255, 0.2); padding: 1.2rem; border-radius: 8px; color: white; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);">
                                        <h4 style="margin: 0 0 0.8rem 0; font-size: 1.1rem; font-weight: 600; color: #ffffff;">{display_name}</h4>
                                        <p style="margin: 0.5rem 0; font-size: 1.2rem; font-weight: bold; color: #e2e8f0;">🗳️ {total_votes:,} votes</p>
                                        <p style="margin: 0; font-size: 1rem; color: #cbd5e0;">🪑 {total_seats} seats | 🏆 {winner[:20]}{"..." if len(winner) > 20 else ""}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                    # Add summary statistics
                    st.markdown("---")
                    summary_cols = st.columns(4)
                    
                    total_all_votes = sum(df['Votes'].sum() for df in councils_data.values())
                    total_all_seats = sum(df['Seats'].sum() for df in councils_data.values())
                    total_parties = sum(len(df) for df in councils_data.values())
                    
                    # with summary_cols[0]:
                    #     st.metric("🗳️ Total Votes (All Councils)", f"{total_all_votes:,}")
                    # with summary_cols[1]:
                    #     st.metric("🪑 Total Seats (All Councils)", f"{total_all_seats}")
                    # with summary_cols[2]:
                    #     st.metric("🏛️ Total Councils", f"{len(councils_data)}")
                    # with summary_cols[3]:
                    #     st.metric("🏃 Total Party Entries", f"{total_parties}")
                
                # Show all councils or selected one
                show_all = True

                # and render your header (or anything else) unconditionally:
                st.header("Comprehensive Council Report")

                
                if show_all:
                    # Display all councils
                    for council_name, council_df in councils_data.items():
                        create_council_summary_and_charts(council_name, council_df)
                else:
                    # Display selected council
                    if selected_council in councils_data:
                        create_council_summary_and_charts(selected_council, councils_data[selected_council])
                        
            else:
                st.error("❌ Could not parse election data. Please check the file format.")
                st.markdown("### 🔍 Debug Information:")
                st.dataframe(df.head(15))
                
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.markdown("### 📋 Raw File Preview:")
            try:
                df = pd.read_excel(uploaded_file)
                st.dataframe(df.head(10))
            except Exception as e2:
                st.error(f"Could not read file: {str(e2)}")
    
    else:
        st.info("👆 Upload your election results Excel file to begin analysis")
        st.markdown("""
        ### 📋 Expected File Format:
        - ✅ Sections numbered like "1 - MANNAR URBAN COUNCIL"
        - ✅ Each section has "Party", "Votes", "Total" columns
        - ✅ Party data in rows below headers
        - ✅ Multiple councils in the same sheet
        """)


if __name__ == "__main__":
    main()


