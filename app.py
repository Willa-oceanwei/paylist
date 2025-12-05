with st.expander("🔍 查詢近四個月資料", expanded=True):
    col1, col2, col3 = st.columns([3,3,1])
    with col1:
        search_customer = st.text_input("輸入客戶名稱")
    with col2:
        date_range = st.date_input(
            "選擇日期區間 (可留空，自動抓本月+前三月)",
            value=[]
        )
    with col3:
        search_btn = st.button("搜尋")

    # 判斷觸發搜尋
    if search_customer or date_range or search_btn:
        filtered = df.copy()
        if search_customer:
            filtered = filtered[filtered['客戶名稱'].str.contains(search_customer, case=False, na=False)]

        if date_range:
            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date = date_range
                end_date = date_range
        else:
            today = pd.Timestamp.today()
            start_date = (today - pd.DateOffset(months=3)).replace(day=1)
            end_date = today

        filtered = filtered[(filtered['日期'] >= start_date) & (filtered['日期'] <= end_date)]

        if not filtered.empty:
            # 日期只顯示年/月/日
            filtered_display = filtered.copy()
            filtered_display['日期'] = filtered_display['日期'].dt.strftime("%Y/%m/%d")
            
            # 依日期由新到舊排序
            filtered_display = filtered_display.sort_values(by='日期', ascending=False)
            
            # 使用 st.dataframe 顯示，指定高度，取消 style
            st.dataframe(filtered_display, use_container_width=True, height=400)
        else:
            st.warning("❌ 沒有符合條件的資料")
