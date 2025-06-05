# pCloud SDK Examples

This directory contains comprehensive examples demonstrating all features and capabilities of the pCloud SDK for Python. Each example is a complete, runnable script that showcases different aspects of the SDK.

## 📁 Example Files Overview

### 🚀 [basic_usage.py](basic_usage.py)
**Perfect starting point for new users**

A simple, straightforward example that covers the essential operations:
- SDK initialization and authentication
- User account information retrieval
- Folder listing and creation
- File upload with progress tracking
- File download and verification
- Basic cleanup operations

**Run it:** `python examples/basic_usage.py`

---

### 🎯 [complete_demo.py](complete_demo.py)
**Comprehensive SDK showcase**

A full-featured demonstration covering all major SDK capabilities:
- Authentication with both direct login and saved credentials
- Account information and quota management
- Advanced folder operations and navigation
- File upload with multiple progress tracker types
- File download with integrity verification
- Complete file operations (rename, move, copy, delete)
- Robust error handling and cleanup
- Best practices demonstration

**Run it:** `python examples/complete_demo.py`

---

### 🔐 [oauth2_example.py](oauth2_example.py)
**OAuth2 authentication flow**

Complete OAuth2 implementation for production applications:
- OAuth2 flow setup and configuration
- Authorization URL generation and browser integration
- Local callback server for authorization code capture
- Code exchange for access tokens
- Token storage and automatic reuse
- Multi-environment support
- Comprehensive error handling

**Prerequisites:** You'll need pCloud app credentials (Client ID/Secret)
**Get credentials:** [pCloud API Documentation](https://docs.pcloud.com/)
**Run it:** `python examples/oauth2_example.py`

---

### 📊 [progress_examples.py](progress_examples.py)
**Progress tracking showcase**

Demonstrates all available progress tracking options:
- **SimpleProgressBar** - Clean visual progress with speed/ETA
- **DetailedProgress** - Comprehensive logging with checkpoints
- **MinimalProgress** - Key milestone notifications only
- **SilentProgress** - Background operation with CSV logging
- **CustomProgress** - Build your own progress tracker
- Performance analysis and comparison
- Real-world usage patterns

**Run it:** `python examples/progress_examples.py`

---

### 🔑 [token_management.py](token_management.py)
**Advanced credential management**

Complete token lifecycle management:
- Automatic token saving and loading
- Manual token extraction and storage
- Multi-account management system
- Token validation and expiration handling
- Security best practices demonstration
- Credential file management
- Cleanup and maintenance operations

**Run it:** `python examples/token_management.py`

---

### ⬆️⬇️ [upload_download_demo.py](upload_download_demo.py)
**File transfer optimization**

Advanced file transfer operations and optimization:
- Basic and advanced upload techniques
- Chunked uploads for large files
- Batch operations for multiple files
- Download with integrity verification
- Performance monitoring and analysis
- Error recovery and retry mechanisms
- Real-world transfer scenarios

**Run it:** `python examples/upload_download_demo.py`

---

## 🚀 Getting Started

### Prerequisites

1. **Install the pCloud SDK:**
   ```bash
   pip install pcloud-sdk
   ```

2. **Have pCloud account credentials ready:**
   - Your pCloud email and password, OR
   - pCloud app credentials (for OAuth2 examples)

### Running Examples

Each example is self-contained and can be run independently:

```bash
# Start with the basic example
python examples/basic_usage.py

# Try the comprehensive demo
python examples/complete_demo.py

# Explore progress tracking
python examples/progress_examples.py
```

### Authentication Methods

The examples support two authentication methods:

#### 1. Direct Login (Email/Password)
Most examples will prompt for your pCloud email and password:
```
📧 Enter your pCloud email: your-email@example.com
🔑 Enter your password: ********
```

#### 2. Environment Variables
Set these to avoid repeated prompts:
```bash
export PCLOUD_EMAIL="your-email@example.com"
export PCLOUD_PASSWORD="your-password"
```

#### 3. OAuth2 (Production Apps)
For the OAuth2 example, you'll need app credentials:
1. Register at [pCloud API](https://docs.pcloud.com/)
2. Get your Client ID and Client Secret
3. Update the credentials in `oauth2_example.py`

---

## 📋 Example Categories

### 🎓 **Learning Examples**
- `basic_usage.py` - Start here for fundamentals
- `complete_demo.py` - Comprehensive overview

### 🔧 **Feature-Specific Examples**
- `progress_examples.py` - Progress tracking options
- `token_management.py` - Credential management
- `upload_download_demo.py` - File transfer optimization

### 🏭 **Production Examples**
- `oauth2_example.py` - Production authentication
- `token_management.py` - Multi-account systems

---

## 💡 Usage Tips

### For Beginners
1. Start with `basic_usage.py` to understand core concepts
2. Move to `complete_demo.py` for comprehensive features
3. Explore specific examples based on your needs

### For Developers
1. Use `oauth2_example.py` for production authentication
2. Implement `token_management.py` patterns for user management
3. Optimize transfers with `upload_download_demo.py` techniques

### For Advanced Users
1. Study `progress_examples.py` for custom progress tracking
2. Implement multi-account systems from `token_management.py`
3. Build robust applications using error handling patterns from all examples

---

## 🔒 Security Notes

- **Never hardcode credentials** in production code
- Use environment variables or secure credential storage
- Implement proper token rotation for long-running applications
- Follow the security practices demonstrated in `token_management.py`

---

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify your email/password
   - Try different server locations (US vs EU)
   - Check your internet connection

2. **Import Errors**
   - Ensure pCloud SDK is installed: `pip install pcloud-sdk`
   - Use Python 3.7 or later

3. **Permission Errors**
   - Check file permissions for token storage
   - Ensure write access to temporary directories

4. **Network Issues**
   - Some examples create local servers (OAuth2)
   - Check firewall settings for port 8080

### Getting Help

- Check the [main documentation](../docs/)
- Review [troubleshooting guide](../docs/TROUBLESHOOTING.md)
- Submit issues on GitHub

---

## 🛠️ Customization

Each example is designed to be easily customizable:

- **Modify authentication methods** in any example
- **Change progress tracking** by swapping progress callbacks
- **Adjust file operations** by modifying folder/file IDs
- **Add custom logic** using the patterns shown

---

## 📚 Next Steps

After exploring these examples:

1. **Read the API documentation** in `docs/API_REFERENCE.md`
2. **Check advanced features** in `docs/`
3. **Build your own applications** using these patterns
4. **Contribute improvements** to the examples

---

## 🤝 Contributing

Found an issue or have an improvement? 

1. Check existing examples for similar patterns
2. Follow the same code style and documentation approach
3. Test thoroughly before submitting
4. Add appropriate error handling and cleanup

---

*Happy coding with pCloud SDK! 🚀*