# Run the application
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 Autonomous Lab TA Backend")
    print("=" * 60)
    print("📊 Database initialized with sample data")
    print("🌐 API ready at http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("=" * 60)
    
    # Fixed: Use import string for reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)