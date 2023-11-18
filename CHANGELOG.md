
### latest

**Added**
 - Basic AsyncApi schema generation

### 0.4.0 (2023-10-27)

**Added**
 - `pre-commit` and `post-commit` consumer mode 

**Updated**
 - TestClient accepts non encoded event

**Removed**
 - `enable_auto_commit` from consumer config

### 0.3.0 (2023-10-17)

**Added**:
 - Message decode logic is moved to a middleware

**Updated**
 - Context obj new field 'decoded_value_cb'
 - **breaking**: request.json is now awaitable

### 0.2.0 (2023-10-14)

**Added**:
 - TestClient

### 0.1.0 (2023-10-10)

initial version