. Authentication (3 Marks)

    [ ] Single-Factor Authentication (1.5m)

        Requirement: "Implementation using password / PIN / username."

        Vajra Feature: The Login Page (/login) using Supabase Auth (Email + Password).

    [ ] Multi-Factor Authentication (1.5m)

        Requirement: "Implementation using at least two factors (e.g., password + OTP)."

        Vajra Feature: The MFA Setup Page (/setup-mfa) and the Download Gate. Users must enter a 6-digit TOTP code (Google Authenticator) to download sensitive files.

2. Authorization (3 Marks)

    [ ] Access Control Model (Theory/Design)

        Requirement: "Implement Access Control Matrix or ACL with minimum 3 subjects and 3 objects."

        Vajra Implementation: You need to define these explicitly in your code/database:

            3 Subjects (Roles): Admin (Commander), Operator (Mission Specialist), Viewer (Ground Staff).

            3 Objects (File Types): Top_Secret_Telemetry (Red), Mission_Logs (Yellow), Public_Reports (Green).

    [ ] Policy Definition & Justification (1.5m)

        Requirement: "Clearly define and justify access rights."

        Vajra Feature: Your Dashboard logic.

            Example: "Only Commanders can DELETE files (Justification: Prevent data loss)."

            Example: "Only Mission Specialists can UPLOAD (Justification: Maintain data quality)."

    [ ] Implementation of Access Control (1.5m)

        Requirement: "Enforce permissions programmatically."

        Vajra Feature: The Python Backend check: if user.role != 'COMMANDER': raise 403.

3. Encryption (3 Marks)

    [ ] Key Exchange Mechanism (1.5m)

        Requirement: "Demonstrate secure key generation or key exchange."

        Vajra Feature: The Python Backend (crypto_utils.py). You are using os.urandom(32) to generate a fresh, cryptographically secure AES key for every single file upload. This counts as "Secure Key Generation."

    [ ] Encryption & Decryption (1.5m)

        Requirement: "Implement secure encryption (AES, RSA...)."

        Vajra Feature: The Sharding Engine. You encrypt chunks using AES-256-GCM before they ever leave the server to go to storage. You decrypt them on the fly during download.

4. Hashing & Digital Signature (3 Marks)

    [ ] Hashing with Salt (1.5m)

        Requirement: "Secure storage of passwords/data using hashing with salt."

        Vajra Feature: Supabase Auth handles the salted password hashing (bcrypt) automatically. Mention this in your report.

    [ ] Digital Signature using Hash (1.5m)

        Requirement: "Demonstrate data integrity... using hash-based digital signatures."

        Vajra Feature: The SHA-256 Chunk Hashing.

            How to sell it: "We generate a SHA-256 hash for every encrypted chunk. When downloading, we re-calculate the hash to verify the file wasn't tampered with in space/transit." (This covers the 'Integrity' requirement).

5. Encoding Techniques (3 Marks)

    [ ] Encoding & Decoding Implementation (1m)

        Requirement: "Base64 / QR Code..."

        Vajra Feature: Two places!

            Base64: You encode the encrypted binary chunks to Base64 strings for storage.

            QR Code: You generate a QR Code on the MFA Setup Page for the user to scan. (Double win!)

    [ ] Security Levels & Risks (Theory) (1m)

        Prep: Be ready to say: "Base64 is NOT encryption; it's just encoding. It increases file size by ~33%, which is a risk for satellite bandwidth, but necessary for text-based transport protocols."

    [ ] Possible Attacks (Theory) (1m)

        Prep: Be ready to mention: "We use AES-GCM to prevent Tampering Attacks and MFA to prevent Credential Stuffing."

6. Viva & Participation (5 Marks)

    [ ] Conceptual Clarity: Do you know why you sharded the file? (To prevent single-point leakage).

    [ ] Defense: Can you explain the flow without looking at the code? (Client -> Python API -> Supabase).