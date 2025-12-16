/**
 * Email Service using Resend
 *
 * Handles welcome emails to new users and admin notifications for signups.
 */

import { Resend } from 'resend';
import { env } from '../config/env.js';
import type { User } from '../types/index.js';

// Initialize Resend client
let resend: Resend | null = null;

function getResendClient(): Resend | null {
  if (!env.RESEND_API_KEY) {
    console.warn('RESEND_API_KEY not configured - emails disabled');
    return null;
  }

  if (!resend) {
    resend = new Resend(env.RESEND_API_KEY);
  }

  return resend;
}

// ============================================================
// EMAIL TEMPLATES
// ============================================================

function getWelcomeEmailHtml(user: User): string {
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome to AML Expert</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 40px; text-align: center;">
              <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">
                Welcome to AML Expert
              </h1>
              <p style="margin: 10px 0 0; color: #bfdbfe; font-size: 16px;">
                Your AI-Powered Compliance Assistant
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 40px;">
              <p style="margin: 0 0 20px; color: #374151; font-size: 18px; line-height: 1.6;">
                Hi ${user.displayName || 'there'},
              </p>

              <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                Welcome to AML Expert! We're excited to have you on board. Your account has been successfully created.
              </p>

              <div style="background-color: #f0f9ff; border-left: 4px solid #3b82f6; padding: 20px; margin: 30px 0; border-radius: 0 8px 8px 0;">
                <h3 style="margin: 0 0 15px; color: #1e40af; font-size: 16px; font-weight: 600;">
                  What you can do with AML Expert:
                </h3>
                <ul style="margin: 0; padding: 0 0 0 20px; color: #4b5563; font-size: 14px; line-height: 1.8;">
                  <li>Ask questions about AML/CFT regulations</li>
                  <li>Get guidance on FATF recommendations</li>
                  <li>Learn about EU AML directives</li>
                  <li>Understand KYC/CDD requirements</li>
                  <li>Review enforcement cases and lessons learned</li>
                </ul>
              </div>

              <p style="margin: 0 0 30px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                Our AI assistant is powered by Claude and has access to thousands of regulatory documents including FATF guidance, EU regulations, and enforcement actions.
              </p>

              <!-- CTA Button -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <a href="${env.CLIENT_URL}/chat" style="display: inline-block; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                      Start Chatting
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
              <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px;">
                Questions? Just reply to this email.
              </p>
              <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                AML Expert - AI-Powered Compliance Intelligence
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
`;
}

function getAdminNotificationHtml(user: User): string {
  const providerEmoji = user.provider === 'google' ? '🔵' : '⚫';
  const signupTime = new Date().toLocaleString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short'
  });

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>New User Signup</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="500" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 30px; text-align: center;">
              <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700;">
                🎉 New User Signup!
              </h1>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 30px;">
              <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9fafb; border-radius: 8px; padding: 20px;">
                <tr>
                  <td style="padding: 10px 20px; border-bottom: 1px solid #e5e7eb;">
                    <span style="color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600;">Name</span>
                    <p style="margin: 5px 0 0; color: #111827; font-size: 16px; font-weight: 500;">
                      ${user.displayName || 'Not provided'}
                    </p>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 10px 20px; border-bottom: 1px solid #e5e7eb;">
                    <span style="color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600;">Email</span>
                    <p style="margin: 5px 0 0; color: #111827; font-size: 16px; font-weight: 500;">
                      ${user.email || 'Not provided'}
                    </p>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 10px 20px; border-bottom: 1px solid #e5e7eb;">
                    <span style="color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600;">Provider</span>
                    <p style="margin: 5px 0 0; color: #111827; font-size: 16px; font-weight: 500;">
                      ${providerEmoji} ${user.provider === 'google' ? 'Google' : 'GitHub'}
                    </p>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 10px 20px;">
                    <span style="color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600;">Signed Up</span>
                    <p style="margin: 5px 0 0; color: #111827; font-size: 16px; font-weight: 500;">
                      ${signupTime}
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
              <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                AML Expert Admin Notification
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
`;
}

// ============================================================
// EMAIL SENDING FUNCTIONS
// ============================================================

/**
 * Send welcome email to a new user
 */
export async function sendWelcomeEmail(user: User): Promise<boolean> {
  const client = getResendClient();
  if (!client) return false;

  if (!user.email) {
    console.warn('Cannot send welcome email: user has no email address');
    return false;
  }

  try {
    const { error } = await client.emails.send({
      from: env.EMAIL_FROM || 'AML Expert <noreply@resend.dev>',
      to: user.email,
      subject: 'Welcome to AML Expert! 🎉',
      html: getWelcomeEmailHtml(user),
    });

    if (error) {
      console.error('Failed to send welcome email:', error);
      return false;
    }

    console.log(`Welcome email sent to ${user.email}`);
    return true;
  } catch (error) {
    console.error('Error sending welcome email:', error);
    return false;
  }
}

/**
 * Send admin notification about new signup
 */
export async function sendAdminSignupNotification(user: User): Promise<boolean> {
  const client = getResendClient();
  if (!client) return false;

  const adminEmail = env.ADMIN_EMAIL;
  if (!adminEmail) {
    console.warn('Cannot send admin notification: ADMIN_EMAIL not configured');
    return false;
  }

  try {
    const { error } = await client.emails.send({
      from: env.EMAIL_FROM || 'AML Expert <noreply@resend.dev>',
      to: adminEmail,
      subject: `🎉 New User: ${user.displayName || user.email || 'Unknown'}`,
      html: getAdminNotificationHtml(user),
    });

    if (error) {
      console.error('Failed to send admin notification:', error);
      return false;
    }

    console.log(`Admin notification sent for new user: ${user.email}`);
    return true;
  } catch (error) {
    console.error('Error sending admin notification:', error);
    return false;
  }
}

/**
 * Send both welcome and admin notification emails for new signups
 */
export async function handleNewUserSignup(user: User): Promise<void> {
  // Send both emails in parallel
  await Promise.all([
    sendWelcomeEmail(user),
    sendAdminSignupNotification(user),
  ]);
}
