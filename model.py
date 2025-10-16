import pandas as pd
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class PropertySearchModel:
    """
    Natural Language Property Search Model for Real Estate Data
    Searches through CSV files based on natural language queries
    """
    
    def __init__(self, project_csv: str, address_csv: str, 
                 config_csv: str, variant_csv: str):
        """
        Initialize the model by loading all CSV files
        
        Args:
            project_csv: Path to project.csv
            address_csv: Path to ProjectAddress.csv
            config_csv: Path to ProjectConfiguration.csv
            variant_csv: Path to ProjectConfigurationVariant.csv
        """
        # Load CSV files with proper handling
        self.df_project = pd.read_csv(project_csv)
        self.df_address = pd.read_csv(address_csv)
        self.df_config = pd.read_csv(config_csv)
        self.df_variant = pd.read_csv(variant_csv)
        
        # Clean column names (remove extra spaces)
        for df in [self.df_project, self.df_address, self.df_config, self.df_variant]:
            df.columns = df.columns.str.strip()
        
        # Create merged dataset
        self.df_merged = self._merge_dataframes()
        
        # City mapping (extend as needed)
        self.city_keywords = {
            'pune': ['pune', 'pimpri', 'chinchwad', 'wakad', 'hinjewadi', 'mamurdi'],
            'mumbai': ['mumbai', 'bombay', 'andheri', 'bandra', 'chembur', 'thane', 'navi mumbai'],
            'bangalore': ['bangalore', 'bengaluru', 'whitefield', 'electronic city'],
            'delhi': ['delhi', 'new delhi', 'gurgaon', 'noida', 'dwarka'],
            'hyderabad': ['hyderabad', 'secunderabad', 'gachibowli', 'hitech city'],
            'chennai': ['chennai', 'madras', 'tambaram'],
            'kolkata': ['kolkata', 'calcutta', 'salt lake']
        }
        
        print(f"✅ Loaded {len(self.df_merged)} property records")
        
    def _merge_dataframes(self) -> pd.DataFrame:
        """Merge all dataframes into a single searchable dataset"""
        # Start with project
        merged = self.df_project.copy()
        
        # Merge with address
        if 'projectId' in self.df_address.columns:
            merged = merged.merge(
                self.df_address, 
                left_on='id', 
                right_on='projectId', 
                how='left',
                suffixes=('', '_address')
            )
        
        # Merge with configuration
        if 'projectId' in self.df_config.columns:
            merged = merged.merge(
                self.df_config,
                left_on='id',
                right_on='projectId',
                how='left',
                suffixes=('', '_config')
            )
        
        # Merge with variant
        config_id_col = 'id_config' if 'id_config' in merged.columns else 'id'
        if 'configurationId' in self.df_variant.columns:
            merged = merged.merge(
                self.df_variant,
                left_on=config_id_col,
                right_on='configurationId',
                how='left',
                suffixes=('', '_variant')
            )
        
        return merged
    
    def parse_query(self, query: str) -> Dict:
        """
        Extract filters from natural language query
        
        Args:
            query: Natural language search query
            
        Returns:
            Dictionary containing extracted filters
        """
        query_lower = query.lower()
        filters = {}
        
        # Extract BHK (1BHK, 2BHK, 3BHK, etc.)
        bhk_match = re.search(r'(\d+)\s*bhk', query_lower)
        if bhk_match:
            filters['bhk'] = int(bhk_match.group(1))
        
        # Extract budget in different formats
        budget_patterns = [
            (r'₹?\s*(\d+\.?\d*)\s*cr(?:ore)?s?', 10000000),  # Crores
            (r'₹?\s*(\d+\.?\d*)\s*la(?:kh|c)s?', 100000),  # Lakhs
            (r'₹?\s*(\d+\.?\d*)\s*l\b', 100000),  # Lakhs (short)
            (r'₹?\s*(\d+\.?\d*)\s*million', 10000000),
        ]
        
        for pattern, multiplier in budget_patterns:
            match = re.search(pattern, query_lower)
            if match:
                amount = float(match.group(1).replace(',', ''))
                filters['max_budget'] = amount * multiplier
                break
        
        # Extract city
        for city, keywords in self.city_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    filters['city'] = city
                    filters['city_keywords'] = keywords
                    break
            if 'city' in filters:
                break
        
        # Extract readiness/possession status
        if any(word in query_lower for word in ['ready', 'immediate', 'ready to move']):
            filters['status'] = 'ready'
        elif any(word in query_lower for word in ['under construction', 'upcoming']):
            filters['status'] = 'under_construction'
        
        # Extract property type
        if 'apartment' in query_lower or 'flat' in query_lower:
            filters['property_type'] = 'apartment'
        elif 'villa' in query_lower:
            filters['property_type'] = 'villa'
        elif 'plot' in query_lower:
            filters['property_type'] = 'plot'
        
        # Extract furnished type
        if 'furnished' in query_lower:
            if 'semi' in query_lower or 'semi-furnished' in query_lower:
                filters['furnished'] = 'SEMI-FURNISHED'
            elif 'unfurnished' in query_lower:
                filters['furnished'] = 'UNFURNISHED'
            else:
                filters['furnished'] = 'FURNISHED'
        
        return filters
    
    def search(self, query: str, limit: int = 10) -> Tuple[pd.DataFrame, Dict]:
        """
        Search properties based on natural language query
        
        Args:
            query: Natural language search query
            limit: Maximum number of results to return
            
        Returns:
            Tuple of (filtered DataFrame, extracted filters)
        """
        filters = self.parse_query(query)
        df_filtered = self.df_merged.copy()
        
        # Remove rows with missing critical data
        df_filtered = df_filtered.dropna(subset=['price'])
        
        
        # Apply BHK filter
        if 'bhk' in filters:
            bhk_value = filters['bhk']
            df_filtered = df_filtered.reset_index(drop=True)  # <--- ADD THIS
            bhk_filter = pd.Series([False] * len(df_filtered))
            
            if 'type' in df_filtered.columns:
                bhk_filter |= (df_filtered['type'] == bhk_value)
            
            if 'customBHK' in df_filtered.columns:
                bhk_filter |= (df_filtered['customBHK'].astype(str).str.contains(
                    f"{bhk_value}BHK", case=False, na=False))
                bhk_filter |= (df_filtered['customBHK'].astype(str).str.contains(
                    f"{bhk_value} BHK", case=False, na=False))
            
            df_filtered = df_filtered[bhk_filter]

        # Apply budget filter
        if 'max_budget' in filters:
            df_filtered = df_filtered[df_filtered['price'] <= filters['max_budget']]
        
        # Apply city filter - search in fullAddress, landmark, and projectName
        if 'city' in filters:
            df_filtered = df_filtered.reset_index(drop=True)  # 👈 FIX added here
            city_keywords = filters.get('city_keywords', [filters['city']])
            city_filter = pd.Series([False] * len(df_filtered))
            
            for keyword in city_keywords:
                if 'fullAddress' in df_filtered.columns:
                    city_filter |= df_filtered['fullAddress'].astype(str).str.contains(
                        keyword, case=False, na=False)
                
                if 'landmark' in df_filtered.columns:
                    city_filter |= df_filtered['landmark'].astype(str).str.contains(
                        keyword, case=False, na=False)
                
                if 'projectName' in df_filtered.columns:
                    city_filter |= df_filtered['projectName'].astype(str).str.contains(
                        keyword, case=False, na=False)
            
            df_filtered = df_filtered[city_filter]

        
        # Apply status filter
        if 'status' in filters and 'status' in df_filtered.columns:
            status_value = filters['status']
            if status_value == 'ready':
                status_keywords = ['ready', 'completed', 'ready to move']
            else:
                status_keywords = ['under construction', 'ongoing', 'upcoming']
            
            status_filter = pd.Series([False] * len(df_filtered))
            for keyword in status_keywords:
                status_filter |= df_filtered['status'].astype(str).str.contains(
                    keyword, case=False, na=False)
            
            df_filtered = df_filtered[status_filter]
        
        # Apply furnished filter
        if 'furnished' in filters and 'furnishedType' in df_filtered.columns:
            df_filtered = df_filtered[
                df_filtered['furnishedType'].astype(str).str.upper() == filters['furnished']
            ]
        
        # Sort by price (ascending)
        # df_filtered = df_filtered.sort_values('price', ascending=True)
        # Sort by relevance: ready > under construction, then price
        if 'status' in df_filtered.columns:
            df_filtered['status_score'] = df_filtered['status'].astype(str).str.contains('ready', case=False, na=False).astype(int)
            df_filtered = df_filtered.sort_values(by=['status_score', 'price'], ascending=[False, True])
            df_filtered = df_filtered.drop(columns=['status_score'])
        else:
            df_filtered = df_filtered.sort_values('price', ascending=True)
        # Remove duplicates and limit results
        if 'projectName' in df_filtered.columns:
            # df_filtered = df_filtered.drop_duplicates(
            #     subset=['projectName', 'type', 'price'], keep='first')
             df_filtered = df_filtered.drop_duplicates(
                 subset=['slug'], keep='first')  # 👈 Slug is unique per project   
        df_filtered = df_filtered.head(limit)
        
        return df_filtered, filters
    
    def generate_summary(self, df_results: pd.DataFrame, filters: Dict) -> str:
        """
        Generate a 2-4 line summary based on search results
        
        Args:
            df_results: Filtered search results
            filters: Extracted filters from query
            
        Returns:
            Summary string
        """
        # if df_results.empty:
        #     return "No properties found matching your criteria. Try adjusting your search parameters."
        if df_results.empty:
            fallback = []
            if 'status' in filters:
                fallback.append("removing the 'ready to move' filter")
            if 'max_budget' in filters:
                fallback.append("increasing your budget")
            if not fallback:
                return "No properties found matching your criteria. Try adjusting your search parameters."
            else:
                return f"No properties found matching your criteria. Try {', and '.join(fallback)} for better results."
        count = len(df_results)
        bhk_info = f"{filters.get('bhk', '')}BHK " if 'bhk' in filters else ""
        city_info = filters.get('city', 'various cities').title()
        
        if 'max_budget' in filters:
            budget = filters['max_budget']
            if budget >= 10000000:
                budget_str = f"₹{budget/10000000:.1f} Cr"
            else:
                budget_str = f"₹{budget/100000:.1f} Lakh"
        else:
            budget_str = "your budget"
        
        min_price = df_results['price'].min()
        max_price = df_results['price'].max()
        
        if max_price >= 10000000:
            if min_price >= 10000000:
                price_range = f"₹{min_price/10000000:.2f} Cr - ₹{max_price/10000000:.2f} Cr"
            else:
                price_range = f"₹{min_price/100000:.1f} Lakh - ₹{max_price/10000000:.2f} Cr"
        else:
            price_range = f"₹{min_price/100000:.2f} Lakh - ₹{max_price/100000:.2f} Lakh"
        
        summary = f"Found {count} {bhk_info}{'properties' if count > 1 else 'property'} in {city_info} under {budget_str}. "
        summary += f"Prices range from {price_range}. "
        
        if count > 5:
            summary += f"Showing top {count} matches with the best value for your requirements."
        else:
            summary += f"These properties offer great value with modern amenities and convenient locations."
        
        return summary
    
    def format_price(self, price: float) -> str:
        """Format price in Indian currency format"""
        if pd.isna(price):
            return "Price on request"
        
        if price >= 10000000:  # Crores
            return f"₹{price/10000000:.2f} Cr"
        elif price >= 100000:  # Lakhs
            return f"₹{price/100000:.2f} Lakh"
        else:
            return f"₹{price:,.0f}"
    
    def get_bhk_display(self, row: pd.Series) -> str:
        """Get BHK display string from row data"""
        if 'customBHK' in row and pd.notna(row['customBHK']):
            return str(row['customBHK'])
        elif 'type' in row and pd.notna(row['type']):
            return f"{int(row['type'])}BHK"
        else:
            return "N/A"
    
    # def extract_city_from_address(self, row: pd.Series) -> str:
    #     """Extract city from address data"""
    #     address = str(row.get('fullAddress', ''))
        
    #     # Check against known cities
    #     for city, keywords in self.city_keywords.items():
    #         for keyword in keywords:
    #             if keyword in address.lower():
    #                 return city.title()
        
    #     # Fallback: try to extract from address
    #     if address and address != 'nan':
    #         parts = [p.strip() for p in address.split(',')]
    #         if len(parts) >= 2:
    #             return parts[-2].strip()
        
    #     return "N/A"
    def extract_city_from_address(self, row: pd.Series) -> str:
        """Extract city from address data"""
        address = str(row.get('fullAddress', '')).strip()

        # Check against known cities
        for city, keywords in self.city_keywords.items():
            for keyword in keywords:
                if keyword in address.lower():
                    return city.title()

        # Fallback: try to extract from address parts
        if address and address.lower() not in ['nan', 'none', '', 'n/a']:
            parts = [p.strip() for p in address.split(',') if p.strip()]
            if parts:
                # Take last non-empty part (most likely city)
                return parts[-1].title()

        return "Not mentioned"

    
    def display_property_cards(self, df_results: pd.DataFrame):
        """
        Display property cards in a formatted manner
        
        Args:
            df_results: Filtered search results
        """
        if df_results.empty:
            print("No properties found.")
            return
        
        print("\n" + "="*80)
        print(f"{'PROPERTY LISTINGS':^80}")
        print("="*80 + "\n")
        
        for idx, (_, row) in enumerate(df_results.iterrows(), 1):
            # Extract data with fallbacks
            project_name = row.get('projectName', 'Untitled Project')
            # city = self.extract_city_from_address(row)
            # locality = row.get('landmark', row.get('fullAddress', 'N/A'))
            city = self.extract_city_from_address(row)
            locality = row.get('landmark') or row.get('fullAddress')

            # --- Handle missing / bad locality ---
            if not isinstance(locality, str) or locality.strip() == '' or locality.lower() in ['nan', 'none', 'n/a', 'unknown', 'not mentioned']:
                locality = "Not mentioned"

            # --- Handle missing / bad city ---
            if not isinstance(city, str) or city.strip() == '' or city.lower() in ['nan', 'none', 'n/a', 'unknown', 'not mentioned']:
                city = "Not mentioned"

            # --- Combine city + locality safely ---
            if city == "Not mentioned" and locality == "Not mentioned":
                location_display = "Location details coming soon"
            else:
                location_display = f"{city}, {locality}"


            # Truncate locality if too long
            if len(str(locality)) > 40:
                locality = str(locality)[:37] + "..."
            
            bhk_type = self.get_bhk_display(row)
            price = self.format_price(row.get('price'))
            status = row.get('status', 'Available')
            carpet_area = row.get('carpetArea', 'N/A')
            
            # Format carpet area
            if pd.notna(carpet_area) and carpet_area != 'N/A':
                carpet_area_str = f"{carpet_area} sq.ft"
            else:
                carpet_area_str = "N/A"
            
            slug = row.get('slug', project_name.lower().replace(' ', '-'))
            
            # Generate CTA URL
            cta_url = f"/project/{slug}"
            
            # Amenities from data
            amenities = []
            if 'lift' in row and str(row['lift']).upper() == 'TRUE':
                amenities.append('Lift')
            if 'balcony' in row and pd.notna(row['balcony']):
                try:
                    bal_count = int(float(row['balcony']))
                    if bal_count > 0:
                        amenities.append(f'{bal_count} Balcony' if bal_count == 1 else f'{bal_count} Balconies')
                except:
                    pass
            if 'bathrooms' in row and pd.notna(row['bathrooms']):
                try:
                    bath_count = int(float(row['bathrooms']))
                    amenities.append(f'{bath_count} Bathroom' if bath_count == 1 else f'{bath_count} Bathrooms')
                except:
                    pass
            
            # Add generic amenities if none found
            if not amenities:
                amenities = ['Modern Amenities', 'Security', 'Parking']
            
            amenities_str = ', '.join(amenities[:4])
            
            # Create card
            print(f"#{idx}")
            print(f"┌{'─'*78}┐")
            print(f"│ {str(project_name)[:74]:<74} │")
            print(f"├{'─'*78}┤")
            # print(f"│ 📍 {city}, {str(locality)[:62]:<62} │")
            print(f"│ 📍 {location_display[:72]:<72} │")
            print(f"│ 🏠 {bhk_type:<20} │ 💰 {price:<20} │ 📐 {carpet_area_str:<17} │")
            furnished = row.get('furnishedType')
            if pd.isna(furnished) or str(furnished).strip() in ['', 'nan', 'none', 'n/a']:
                furnished = "Not mentioned"

            print(f"│ 🔑 Status: {str(status)[:30]:<30} │ 🛋️  {furnished:<25} │")

            # print(f"│ 🔑 Status: {str(status)[:30]:<30} │ 🛋️  {row.get('furnishedType', 'N/A'):<25} │")
            print(f"│ ✨ {amenities_str[:72]:<72} │")
            # print(f"│ 🔗 {cta_url:<74]} │")
            print(f"│ 🔗 {cta_url:<74} │")
            print(f"└{'─'*78}┘\n")
    
    def run_query(self, query: str, limit: int = 10):
        """
        Complete workflow: parse query, search, summarize, and display
        
        Args:
            query: Natural language search query
            limit: Maximum number of results
        """
        print(f"\n🔍 Searching for: '{query}'\n")
        
        # Search
        df_results, filters = self.search(query, limit)
        
        # Display extracted filters
        print("📋 Extracted Filters:")
        for key, value in filters.items():
            if key != 'city_keywords':  # Skip internal helper
                print(f"   • {key.replace('_', ' ').title()}: {value}")
        print()
        
        # Generate and display summary
        summary = self.generate_summary(df_results, filters)
        print("📊 Summary:")
        print(f"   {summary}\n")
        
        # Display property cards
        self.display_property_cards(df_results)
        
        return df_results


# Example Usage
if __name__ == "__main__":
    # Initialize the model
    model = PropertySearchModel(
        project_csv='C:/Users/kisha/OneDrive/Desktop/NoBrokerage_BOT/data/project.csv',
        address_csv='C:/Users/kisha/OneDrive/Desktop/NoBrokerage_BOT/data/ProjectAddress.csv',
        config_csv='C:/Users/kisha/OneDrive/Desktop/NoBrokerage_BOT/data/ProjectConfiguration.csv',
        variant_csv='C:/Users/kisha/OneDrive/Desktop/NoBrokerage_BOT/data/ProjectConfigurationVariant.csv'
    )
    
    # Example queries
    queries = [
        "3BHK flat in Pune under ₹1.2 Cr",
        "2BHK apartment in Mumbai ready to move under 80 lakh",
        "Show me properties in Chembur"
    ]
    
    for query in queries:
        
        model.run_query(query, limit=5)
        print("\n" + "="*80 + "\n")