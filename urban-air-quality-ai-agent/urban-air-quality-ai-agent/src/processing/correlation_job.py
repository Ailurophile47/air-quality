"""
Spark Job for Correlation Analysis
Analyzes correlation between AQI, traffic, and weather data
Generates insights and stores results in PostgreSQL
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, avg, max as spark_max, min as spark_min,
    hour, corr, count, round as spark_round
)
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType,
    IntegerType, TimestampType
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CorrelationAnalysisJob:
    """
    Spark job for analyzing correlations between environmental factors
    """
    
    def __init__(self):
        """Initialize Spark session and database configuration"""
        self.spark = self._create_spark_session()
        
        # PostgreSQL configuration
        self.db_host = os.getenv('POSTGRES_HOST', 'postgres')
        self.db_port = os.getenv('POSTGRES_PORT', '5432')
        self.db_name = os.getenv('POSTGRES_DB', 'urban_air_quality')
        self.db_user = os.getenv('POSTGRES_USER', 'airquality')
        self.db_password = os.getenv('POSTGRES_PASSWORD', 'postgres123')
        
        self.jdbc_url = f"jdbc:postgresql://{self.db_host}:{self.db_port}/{self.db_name}"
        self.jdbc_properties = {
            "user": self.db_user,
            "password": self.db_password,
            "driver": "org.postgresql.Driver"
        }
    
    def _create_spark_session(self) -> SparkSession:
        """Create and configure Spark session"""
        spark = SparkSession.builder \
            .appName("AirQuality-Correlation-Analysis") \
            .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        # Set log level to reduce verbosity
        spark.sparkContext.setLogLevel("WARN")
        
        print("✅ Spark session created successfully")
        return spark
    
    def load_data_from_postgres(self, table_name: str, hours_back: int = 24):
        """
        Load data from PostgreSQL table
        
        Args:
            table_name: Name of the table to load
            hours_back: Number of hours of historical data to load
            
        Returns:
            Spark DataFrame
        """
        try:
            # Calculate time filter
            time_filter = datetime.utcnow() - timedelta(hours=hours_back)
            
            query = f"""
                (SELECT * FROM {table_name} 
                 WHERE timestamp >= '{time_filter.isoformat()}'
                ) as filtered_data
            """
            
            df = self.spark.read.jdbc(
                url=self.jdbc_url,
                table=query,
                properties=self.jdbc_properties
            )
            
            print(f"✅ Loaded {df.count()} records from {table_name}")
            return df
            
        except Exception as e:
            print(f"❌ Error loading data from {table_name}: {e}")
            return None
    
    def calculate_correlations(self, aqi_df, weather_df, traffic_df, location: str):
        """
        Calculate correlations for a specific location
        
        Args:
            aqi_df: AQI DataFrame
            weather_df: Weather DataFrame
            traffic_df: Traffic DataFrame
            location: Location name
            
        Returns:
            Dictionary with correlation results
        """
        try:
            # Filter by location
            aqi_loc = aqi_df.filter(col("location") == location)
            weather_loc = weather_df.filter(col("location") == location)
            traffic_loc = traffic_df.filter(col("location") == location)
            
            # Join datasets on timestamp (with tolerance of 5 minutes)
            # First, create hour-based keys for joining
            aqi_hourly = aqi_loc.withColumn("hour_key", hour(col("timestamp")))
            weather_hourly = weather_loc.withColumn("hour_key", hour(col("timestamp")))
            traffic_hourly = traffic_loc.withColumn("hour_key", hour(col("timestamp")))
            
            # Join AQI with Traffic
            aqi_traffic = aqi_hourly.join(
                traffic_hourly,
                ["location", "hour_key"],
                "inner"
            ).select(
                col("location"),
                aqi_hourly["timestamp"].alias("aqi_timestamp"),
                col("aqi"),
                col("pm25"),
                col("congestion_score"),
                col("average_speed"),
                col("hour_key")
            )
            
            # Join with Weather
            combined = aqi_traffic.join(
                weather_hourly,
                ["location", "hour_key"],
                "inner"
            ).select(
                col("location"),
                col("aqi_timestamp").alias("timestamp"),
                col("aqi"),
                col("pm25"),
                col("congestion_score"),
                col("average_speed"),
                col("temperature"),
                col("humidity"),
                col("wind_speed"),
                col("hour_key")
            )
            
            if combined.count() == 0:
                print(f"⚠️  No joined data for {location}")
                return None
            
            # Calculate correlations
            correlations = {}
            
            # AQI vs Traffic
            aqi_traffic_corr = combined.select(
                corr("aqi", "congestion_score").alias("correlation")
            ).collect()[0]["correlation"]
            correlations["aqi_traffic"] = round(aqi_traffic_corr, 4) if aqi_traffic_corr else 0.0
            
            # AQI vs Temperature
            aqi_temp_corr = combined.select(
                corr("aqi", "temperature").alias("correlation")
            ).collect()[0]["correlation"]
            correlations["aqi_temperature"] = round(aqi_temp_corr, 4) if aqi_temp_corr else 0.0
            
            # AQI vs Humidity
            aqi_humidity_corr = combined.select(
                corr("aqi", "humidity").alias("correlation")
            ).collect()[0]["correlation"]
            correlations["aqi_humidity"] = round(aqi_humidity_corr, 4) if aqi_humidity_corr else 0.0
            
            # AQI vs Wind Speed
            aqi_wind_corr = combined.select(
                corr("aqi", "wind_speed").alias("correlation")
            ).collect()[0]["correlation"]
            correlations["aqi_wind"] = round(aqi_wind_corr, 4) if aqi_wind_corr else 0.0
            
            # Calculate statistics
            stats = combined.agg(
                avg("aqi").alias("avg_aqi"),
                spark_max("aqi").alias("max_aqi"),
                spark_min("aqi").alias("min_aqi"),
                avg("congestion_score").alias("avg_traffic_score")
            ).collect()[0]
            
            # Find peak hours
            hourly_aqi = combined.groupBy("hour_key").agg(
                avg("aqi").alias("avg_aqi")
            ).orderBy(col("avg_aqi").desc())
            peak_pollution_hour = hourly_aqi.first()["hour_key"]
            
            hourly_traffic = combined.groupBy("hour_key").agg(
                avg("congestion_score").alias("avg_congestion")
            ).orderBy(col("avg_congestion").desc())
            peak_traffic_hour = hourly_traffic.first()["hour_key"]
            
            # Generate insight summary
            insight = self._generate_insight(
                location=location,
                correlations=correlations,
                stats=stats,
                peak_pollution_hour=peak_pollution_hour,
                peak_traffic_hour=peak_traffic_hour
            )
            
            result = {
                "location": location,
                "aqi_traffic_correlation": correlations["aqi_traffic"],
                "aqi_temperature_correlation": correlations["aqi_temperature"],
                "aqi_humidity_correlation": correlations["aqi_humidity"],
                "aqi_wind_correlation": correlations["aqi_wind"],
                "avg_aqi": float(stats["avg_aqi"]),
                "max_aqi": int(stats["max_aqi"]),
                "min_aqi": int(stats["min_aqi"]),
                "avg_traffic_score": float(stats["avg_traffic_score"]),
                "peak_pollution_hour": int(peak_pollution_hour),
                "peak_traffic_hour": int(peak_traffic_hour),
                "insight_summary": insight,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "job_id": f"correlation_job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
            print(f"✅ Correlations calculated for {location}")
            return result
            
        except Exception as e:
            print(f"❌ Error calculating correlations for {location}: {e}")
            return None
    
    def _generate_insight(self, location: str, correlations: Dict, stats, 
                         peak_pollution_hour: int, peak_traffic_hour: int) -> str:
        """
        Generate human-readable insight summary
        
        Args:
            location: Location name
            correlations: Dictionary of correlation coefficients
            stats: Statistical aggregations
            peak_pollution_hour: Hour with highest pollution
            peak_traffic_hour: Hour with highest traffic
            
        Returns:
            Insight summary string
        """
        insights = []
        
        # Traffic correlation insight
        if correlations["aqi_traffic"] > 0.5:
            insights.append(
                f"Strong positive correlation ({correlations['aqi_traffic']:.2f}) "
                f"between traffic and AQI in {location}."
            )
        elif correlations["aqi_traffic"] > 0.3:
            insights.append(
                f"Moderate correlation ({correlations['aqi_traffic']:.2f}) "
                f"between traffic congestion and air quality."
            )
        
        # Peak hours insight
        if abs(peak_pollution_hour - peak_traffic_hour) <= 1:
            insights.append(
                f"Pollution peaks at {peak_pollution_hour}:00, "
                f"coinciding with peak traffic hours."
            )
        
        # AQI level insight
        avg_aqi = stats["avg_aqi"]
        if avg_aqi > 150:
            insights.append(f"Average AQI of {avg_aqi:.0f} indicates unhealthy air quality.")
        elif avg_aqi > 100:
            insights.append(f"Average AQI of {avg_aqi:.0f} is at moderate levels.")
        
        # Weather correlation
        if correlations["aqi_wind"] < -0.3:
            insights.append(
                f"Wind speed shows negative correlation ({correlations['aqi_wind']:.2f}), "
                f"helping disperse pollutants."
            )
        
        return " ".join(insights) if insights else "Insufficient data for insights."
    
    def save_results_to_postgres(self, results: list) -> None:
        """
        Save correlation analysis results to PostgreSQL
        
        Args:
            results: List of result dictionaries
        """
        try:
            if not results:
                print("⚠️  No results to save")
                return
            
            # Convert to Spark DataFrame
            schema = StructType([
                StructField("location", StringType(), False),
                StructField("aqi_traffic_correlation", FloatType(), True),
                StructField("aqi_temperature_correlation", FloatType(), True),
                StructField("aqi_humidity_correlation", FloatType(), True),
                StructField("aqi_wind_correlation", FloatType(), True),
                StructField("avg_aqi", FloatType(), True),
                StructField("max_aqi", IntegerType(), True),
                StructField("min_aqi", IntegerType(), True),
                StructField("avg_traffic_score", FloatType(), True),
                StructField("peak_pollution_hour", IntegerType(), True),
                StructField("peak_traffic_hour", IntegerType(), True),
                StructField("insight_summary", StringType(), True),
                StructField("analysis_timestamp", StringType(), False),
                StructField("job_id", StringType(), True)
            ])
            
            results_df = self.spark.createDataFrame(results, schema=schema)
            
            # Add time range columns
            time_now = datetime.utcnow()
            time_24h_ago = time_now - timedelta(hours=24)
            
            results_df = results_df.withColumn("start_time", col("analysis_timestamp")) \
                                   .withColumn("end_time", col("analysis_timestamp"))
            
            # Write to PostgreSQL (append mode)
            results_df.write.jdbc(
                url=self.jdbc_url,
                table="correlation_analysis",
                mode="append",
                properties=self.jdbc_properties
            )
            
            print(f"✅ Saved {len(results)} correlation results to PostgreSQL")
            
        except Exception as e:
            print(f"❌ Error saving results to PostgreSQL: {e}")
    
    def run(self, hours_back: int = 24) -> None:
        """
        Execute the correlation analysis job
        
        Args:
            hours_back: Number of hours of historical data to analyze
        """
        print(f"\n🚀 Starting Correlation Analysis Job")
        print(f"📅 Analyzing last {hours_back} hours of data")
        print(f"🔗 Database: {self.jdbc_url}\n")
        
        try:
            # Load data from PostgreSQL
            print("📊 Loading data from PostgreSQL...")
            aqi_df = self.load_data_from_postgres("aqi_data", hours_back)
            weather_df = self.load_data_from_postgres("weather_data", hours_back)
            traffic_df = self.load_data_from_postgres("traffic_data", hours_back)
            
            if aqi_df is None or weather_df is None or traffic_df is None:
                print("❌ Failed to load data. Exiting.")
                return
            
            # Get unique locations
            locations = [row["location"] for row in aqi_df.select("location").distinct().collect()]
            print(f"📍 Analyzing {len(locations)} locations: {locations}\n")
            
            # Calculate correlations for each location
            results = []
            for location in locations:
                print(f"🔍 Analyzing {location}...")
                result = self.calculate_correlations(aqi_df, weather_df, traffic_df, location)
                if result:
                    results.append(result)
                    print(f"   AQI-Traffic Correlation: {result['aqi_traffic_correlation']:.4f}")
                    print(f"   Average AQI: {result['avg_aqi']:.2f}")
                    print(f"   Peak Pollution Hour: {result['peak_pollution_hour']}:00")
                    print()
            
            # Save results
            if results:
                print("💾 Saving results to PostgreSQL...")
                self.save_results_to_postgres(results)
                print(f"\n✅ Job completed successfully! Analyzed {len(results)} locations.")
            else:
                print("⚠️  No results generated. Check if sufficient data is available.")
            
        except Exception as e:
            print(f"❌ Job failed: {e}")
            raise
        finally:
            self.spark.stop()
            print("✅ Spark session stopped")


def main():
    """Main entry point"""
    job = CorrelationAnalysisJob()
    job.run(hours_back=24)


if __name__ == "__main__":
    main()