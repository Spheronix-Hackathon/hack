# Spheronix Hackathon - UPI Payment Limit Issue & Resolution Document

**Document Version:** 1.0  
**Date:** October 24, 2026  
**Target Organization:** SPHERONIX TECHNOLOGY PRIVATE LIMITED  
**Merchant UPI ID:** `334509931804612@cnrb` (Canara Bank)  
**Applicable Event:** National Level Tech Hackathon 2026 Registration  

---

## 1. Executive Summary

During student registration for the National Level Tech Hackathon, students attempting to pay the registration fee (₹399.00) via UPI apps (Google Pay, PhonePe, Paytm, BHIM) receive the following banking error:

> **"Your money has not been debited. You've exceeded the bank limit for this payment."**  
> **"Payment Limit Reached - No money has been debited as you've reached the UPI payment limit set by your bank. Please try again after 24 hours or use a different bank account to pay now."**

This document provides a pin-to-point technical and financial explanation of the issue, immediate actions to take today, and the permanent resolution for scaling to 10,000+ registrations.

---

## 2. Pin-to-Point Root Cause Breakdown

### A. Primary Cause: Receiver Account (Canara Bank) Inward Velocity Limit
1. **Daily Inward Count Threshold**:
   - The UPI VPA `334509931804612@cnrb` is registered as a standard/retail UPI endpoint.
   - Standard Canara Bank and NPCI rules restrict standard accounts to **20 to 50 inward transactions per 24 hours**.
   - When 50+ students pay ₹399 within a single day, the bank's automated switch flags the threshold as reached and rejects all subsequent incoming payments.
2. **Daily Credit Volume Cap**:
   - Standard business accounts without custom high-volume merchant profiles have daily credit limits (often ₹50,000 to ₹1,00,000 total per day).
3. **Automated Anti-Fraud Velocity Lock**:
   - Rapid influx of identical small amounts (₹399 repeated within seconds/minutes from different individual remitters across India) triggers bank risk management systems, temporarily freezing incoming UPI credits for 24 hours.

### B. Secondary Cause: Remitter (Student) Bank Limits
1. **Student Account Daily UPI Cap**:
   - NPCI limits individual users to max 10 to 20 UPI transactions per day across all apps.
2. **Device / PIN Reset Cooling Period**:
   - RBI mandates that any user who installed a UPI app on a new device, changed bank SIM, or reset their UPI PIN within the last 24 hours is capped at a maximum of ₹5,000 and 5 transactions.

---

## 3. What We Must Do Right Now (Immediate Action Plan)

### Action 1: Add Direct Bank Transfer (IMPS / NEFT) on Website
Enable students whose UPI is failing to transfer directly to the corporate bank account:
* **Beneficiary Name:** SPHERONIX TECHNOLOGY PVT. LTD.
* **Bank Name:** CANARA BANK
* **Account Number:** `120036804612`
* **IFSC Code:** `CNRB0000659`
* **Account Type:** Current Account

**Student Verification Flow:**
1. Student uses NetBanking or Mobile Banking app to send ₹399 via IMPS/NEFT.
2. The bank SMS / app displays a 12-digit **UTR number** (e.g., `487499545986`).
3. Student enters the 12-digit UTR on the website and uploads screenshot/receipt.
4. Registration verifies and confirms immediately.

---

### Action 2: Add a Secondary / Rotating Backup UPI ID
If Spheronix holds an alternate corporate or official bank account (e.g., HDFC, ICICI, SBI, Axis):
1. Open the `.env` configuration file on the AWS server:
   ```bash
   nano /home/ubuntu/hack/.env
   ```
2. Update the `UPI_ID` field:
   ```env
   UPI_ID=secondary_account@bank
   UPI_PAYEE_NAME=Spheronix Hackathon
   ```
3. Reload backend services:
   ```bash
   sudo systemctl restart hackathon@8000 hackathon@8001
   ```
4. New student payments will immediately route to the fresh bank account with 0 limits used.

---

### Action 3: Display Clear Guidance for Students on Payment Step
Post a clear message for students encountering the limit:
* *"If Google Pay says 'Bank limit reached', please use PhonePe or Paytm, or pay using a family member's account."*
* *"Alternatively, pay via Direct IMPS transfer to our Canara Bank Account and enter the 12-digit UTR."*

---

## 4. Permanent Fix: High-Volume Hackathon Scaling (10,000+ Students)

To accept payments from 10,000+ students without hitting banking limits:

### Option A: Upgrade to Canara Bank Merchant QR (Corporate Education Profile)
Contact your Canara Bank Branch Manager with the draft letter in Section 5 below:
* Request an **Official Merchant UPI QR Code** with MCC (Merchant Category Code) `8299` (Educational Services) or `7399` (Business Services).
* **Benefits:**
  * **Unlimited Inward Transactions**: No 50/day count limits.
  * **Direct Current Account Auto-Settlement**: Funds credit in real-time.
  * **Zero daily credit ceiling**.

### Option B: Payment Gateway Integration (Cashfree / Razorpay)
* The codebase already has integration hooks for **Cashfree** and **Razorpay**.
* Payment Gateways collect through RBI-regulated nodal escrow accounts:
  * Eliminates single-account UPI inward limits entirely.
  * Supports UPI, Credit Card, Debit Card, NetBanking, and UPI Autopay.

---

## 5. Ready-to-Use Canara Bank Request Letter / Email Template

Copy and send this email/letter to your Canara Bank Branch Manager:

```text
To,
The Branch Manager,
Canara Bank

Subject: Request to Upgrade UPI Inward Transaction Limits for Current Account 120036804612

Dear Sir/Madam,

We maintain Current Account No: 120036804612 (IFSC: CNRB0000659) in the name of SPHERONIX TECHNOLOGY PRIVATE LIMITED with your branch.

We are currently hosting a National Level Technical Hackathon with over 5,000+ expected student participants from across India. Participants are making registration fee payments of ₹399 via our UPI ID: 334509931804612@cnrb.

Today, multiple students are receiving the following error:
"You've exceeded the bank limit for this payment / Payment Limit Reached."

We request you to kindly:
1. Lift / increase the daily inward transaction count and volume limits on our UPI ID 334509931804612@cnrb and Account 120036804612.
2. Enable Corporate Merchant Inward Tier / Merchant QR code for our Current Account without daily transaction count restrictions (MCC 8299 - Educational Services).

Kindly process this request on priority to avoid disruption to incoming student registrations.

Thanking you,
Yours faithfully,
For SPHERONIX TECHNOLOGY PRIVATE LIMITED

Authorized Signatory
Contact: [Your Phone Number]
```

---

## 6. Student Support Message Template (For WhatsApp / Support Desk)

Copy and share this with any student reporting the bank limit error:

```text
Dear Participant,

If your UPI app displays "You've exceeded the bank limit for this payment":

1. Quickest Fix: Try paying using PhonePe or Paytm instead of Google Pay, or pay using a family member's UPI app.
2. Direct Bank Transfer: You can also transfer ₹399 directly via IMPS to our official bank account:
   - Account Name: SPHERONIX TECHNOLOGY PVT. LTD.
   - Bank: CANARA BANK
   - Account Number: 120036804612
   - IFSC Code: CNRB0000659
3. Enter the 12-digit UTR / Reference number on the registration portal and upload your payment receipt to complete your registration instantly.

Spheronix Hackathon Support Team
```
