# SQL Ledger Security Notes

This document outlines security considerations and recommendations for the SQL Ledger application.

## 1. Data Encryption

### 1.1. Encryption in Transit
All communication channels should be secured using strong encryption protocols:
-   **Database Connections:** Client-server connections to the PostgreSQL database must use SSL/TLS to protect data from eavesdropping or tampering. This should be enforced in the PostgreSQL server configuration (`pg_hba.conf` and `postgresql.conf` to require SSL) and configured in all client applications (e.g., Python backend using `psycopg2` with `sslmode='require'` or `'verify-full'`).
-   **API Endpoints (Future):** When API endpoints are developed (e.g., for a web front-end or mobile app), they must use HTTPS (HTTP Secure) with up-to-date TLS versions (e.g., TLS 1.2 or TLS 1.3) and strong cipher suites.
-   **Internal Microservices (Future):** If the application evolves into a microservices architecture, all internal service-to-service communication should also be encrypted, for instance, using mTLS.

### 1.2. Encryption at Rest
Protecting data stored on disk is crucial:
-   **Database-Level Encryption:**
    *   **PostgreSQL Transparent Data Encryption (TDE):** Tools like `pgcrypto` can be used for column-level encryption within the database. Some cloud providers offer managed PostgreSQL services with built-in TDE for the entire database instance. For self-hosted PostgreSQL, third-party extensions or solutions (e.g., Cybertec TDE) might be considered, though native full TDE is not a standard PostgreSQL feature as of current versions.
    *   **Data Masking:** For non-production environments, sensitive data should be masked or anonymized.
-   **Filesystem-Level Encryption:** Encrypting the underlying filesystem where the database stores its files (e.g., using LUKS on Linux, BitLocker on Windows, or provider-specific encryption for cloud storage volumes like AWS EBS encryption) adds a strong layer of protection against physical media theft.
-   **Backup Encryption:** All database backups must be encrypted, both during transit to backup storage and at rest in the backup location.

### 1.3. Application-Level Encryption for Sensitive PII
Certain Personally Identifiable Information (PII) fields might require application-level encryption before being stored in the database for maximum security, especially to protect against database administrators or attackers with SQL access.
-   **Identified PII Fields (Current Schema):**
    *   `customers.email`
    *   `customers.phone_number`
    *   `customers.address`
    *   `users.email` (from `auth_schema.sql`)
    *   `users.username` (if considered sensitive, though often used for login)
-   **Implementation:** Use strong, authenticated encryption algorithms (e.g., AES-GCM) with a robust library.
-   **Trade-offs:**
    *   **Searchability:** Encrypting data at the application level makes direct SQL querying on the encrypted fields (e.g., `WHERE email = '...'`) impossible or very complex. Searching would require decrypting data in the application or using specialized searchable encryption schemes (which are complex). For some fields, partial encryption or tokenization might be alternatives if exact match searching is needed.
    *   **Performance:** Application-level encryption/decryption adds computational overhead.
    *   **Key Management:** This is the most critical aspect. Securely managing encryption keys is paramount.

## 2. Key Management
If application-level encryption is implemented, or for managing TDE keys:
-   **Dedicated Key Management System (KMS):** Use a hardware security module (HSM) or a managed KMS solution (e.g., AWS KMS, Google Cloud KMS, Azure Key Vault).
-   **Key Rotation:** Implement policies for regular key rotation.
-   **Access Control:** Strictly limit access to encryption keys.
-   **Key Backup and Recovery:** Ensure keys are securely backed up and can be recovered.

## 3. Password Management
-   **Secure Hashing:** The `users.password_hash` column must store passwords that have been hashed using a strong, adaptive, and salted hashing algorithm.
    *   **Recommended Algorithms:** Argon2 (current best practice), scrypt, or bcrypt.
    *   **DO NOT USE:** MD5, SHA1, SHA256 (or other fast hashes) directly for passwords.
-   **Salt:** A unique salt must be generated for each user and stored alongside the hash or incorporated into it. Most modern password hashing libraries handle this automatically.
-   **Password Policies:** Enforce strong password policies (length, complexity, non-reuse) and consider multi-factor authentication (MFA).

## 4. Audit Trails
-   The `transactions` table provides an audit trail for all financial movements, recording changes to account balances.
-   The `audit_log` table (from `schema_audit.sql`) is designed to capture non-transactional auditable events, such as:
    *   Updates to customer PII (e.g., email, address changes).
    *   Changes to account status (e.g., active, frozen, closed) not directly resulting from a transaction.
    *   User management actions (e.g., user creation, role changes, password resets - though password reset events should not log the password itself).
    *   Significant system events or configuration changes.
-   Ensure `user_id` is captured in `audit_log` whenever an action is user-initiated. System-initiated actions can have a null or a dedicated system user ID.
-   Audit logs should be protected from tampering and retained according to regulatory requirements.

## 5. Access Control (RBAC)
-   The schema defined in `auth_schema.sql` provides a foundation for Role-Based Access Control.
-   **Principle of Least Privilege:** Users should only be granted the permissions necessary to perform their job functions. Roles should be carefully defined with the minimum set of required permissions.
-   Regular review of user roles and permissions is recommended.

## 6. Input Validation and Output Encoding
-   **SQL Injection Prevention:** All database queries must use parameterized statements (prepared statements) to prevent SQL injection vulnerabilities. The current use of `psycopg2` with parameter substitution (e.g., `cur.execute("... WHERE id = %s", (id_val,))`) is good practice.
-   **Cross-Site Scripting (XSS) Prevention (Future API/UI):** When data is displayed in web interfaces, ensure proper output encoding is performed to prevent XSS.
-   **Input Validation:** All data received from external sources (users, other systems) must be rigorously validated for type, format, length, and range.

## 7. Regular Security Audits and Penetration Testing
-   Conduct regular security audits of the codebase and infrastructure.
-   Perform periodic penetration testing by qualified security professionals to identify and remediate vulnerabilities.

## 8. Dependency Management
-   Keep all software dependencies (OS, database, Python libraries, etc.) up-to-date with the latest security patches.
-   Use tools to scan for known vulnerabilities in dependencies.

This document should be reviewed and updated regularly as the SQL Ledger application evolves.
```
