const nodemailer = require('nodemailer');

// Parse command-line arguments
// Usage: node send-email.js <code> <recipient> <sender> <app_password>
const args = process.argv.slice(2);
const verificationCode = args[0] || Math.floor(100000 + Math.random() * 900000).toString();
const recipientEmail = args[1] || 'karthik.maniam008@gmail.com';
const senderEmail = args[2] || 'karthik.maniam008@gmail.com';
const appPassword = args[3] || 'rpjz ujsm cwbp tjxk';

// Create transporter with Gmail SMTP
const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: senderEmail,
    pass: appPassword
  }
});

// Beautiful HTML email template
const htmlTemplate = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);">
  <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%); padding: 40px 20px;">
    <tr>
      <td align="center">
        <!-- Main container -->
        <table width="600" cellpadding="0" cellspacing="0" style="background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); border-radius: 24px; border: 1px solid rgba(139, 92, 246, 0.2); box-shadow: 0 20px 60px rgba(139, 92, 246, 0.15);">
          
          <!-- Header with gradient -->
          <tr>
            <td style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); padding: 40px; text-align: center; border-radius: 24px 24px 0 0;">
              <h1 style="margin: 0; color: #ffffff; font-size: 42px; font-weight: 700; letter-spacing: 2px; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">
                ⚡ VAJRA
              </h1>
              <p style="margin: 10px 0 0; color: rgba(255, 255, 255, 0.9); font-size: 14px; letter-spacing: 1px; text-transform: uppercase;">
                Zero-Trust Security System
              </p>
            </td>
          </tr>
          
          <!-- Content -->
          <tr>
            <td style="padding: 50px 40px;">
              <h2 style="margin: 0 0 20px; color: #ffffff; font-size: 24px; font-weight: 600;">
                Your Verification Code
              </h2>
              
              <p style="margin: 0 0 30px; color: rgba(255, 255, 255, 0.7); font-size: 16px; line-height: 1.6;">
                Use the code below to complete your authentication. This code will expire in 10 minutes for security purposes.
              </p>
              
              <!-- Verification Code Box -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                <tr>
                  <td align="center" style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%); border: 2px solid rgba(139, 92, 246, 0.4); border-radius: 16px; padding: 30px;">
                    <div style="font-size: 48px; font-weight: 700; letter-spacing: 12px; color: #8b5cf6; text-shadow: 0 0 20px rgba(139, 92, 246, 0.5);">
                      ${verificationCode}
                    </div>
                  </td>
                </tr>
              </table>
              
              <!-- Security notice -->
              <div style="margin-top: 40px; padding: 20px; background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; border-radius: 8px;">
                <p style="margin: 0; color: rgba(255, 255, 255, 0.8); font-size: 14px; line-height: 1.6;">
                  🔒 <strong>Security Notice:</strong> Never share this code with anyone. Vajra will never ask for your verification code.
                </p>
              </div>
              
              <p style="margin: 30px 0 0; color: rgba(255, 255, 255, 0.5); font-size: 14px; line-height: 1.6;">
                If you didn't request this code, please ignore this email or contact support if you have concerns.
              </p>
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="padding: 30px 40px; border-top: 1px solid rgba(139, 92, 246, 0.2); text-align: center;">
              <p style="margin: 0 0 10px; color: rgba(255, 255, 255, 0.4); font-size: 12px;">
                Powered by Vajra Zero-Trust Encryption System
              </p>
              <p style="margin: 0; color: rgba(255, 255, 255, 0.3); font-size: 11px;">
                Quantum-Resistant | Fragmentation-Based Architecture | Role-Based Access Control
              </p>
            </td>
          </tr>
          
        </table>
        
        <!-- Footer text outside box -->
        <p style="margin: 20px 0 0; color: rgba(255, 255, 255, 0.3); font-size: 12px; text-align: center;">
          © ${new Date().getFullYear()} Vajra Security. All rights reserved.
        </p>
      </td>
    </tr>
  </table>
</body>
</html>
`;

// Email options
const mailOptions = {
  from: `Vajra Security <${senderEmail}>`,
  to: recipientEmail,

  subject: '⚡ Your Vajra Verification Code',
  text: `Your Vajra verification code is: ${verificationCode}\n\nThis code will expire in 10 minutes.\n\nNever share this code with anyone. Vajra will never ask for your verification code.`,
  html: htmlTemplate
};

// Send email
transporter.sendMail(mailOptions, (error, info) => {
  if (error) {
    console.error('Error sending email:', error);
  } else {
    console.log('✅ Email sent successfully!');
    console.log('📧 Verification Code:', verificationCode);
    console.log('🆔 Message ID:', info.messageId);
    console.log('📨 Response:', info.response);
  }
});
