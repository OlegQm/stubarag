<!DOCTYPE html>
<html>
<head>
    <title>Email Address Verification</title>
    <style>
        body {
            font-family: Georgia, serif;
            background-color: #f8f8f8;
            color: #333;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background: #fff;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        .logo {
            width: 40%;
            max-width: 400px;
            display: block;
            margin: 0 auto;
            margin-bottom: 35px;
            margin-top: 20px;
        }
        h1 {
            color: #0039A6;
            font-size: 22px;
            text-align: center;
            border-bottom: 2px solid #0039A6;
            padding-bottom: 8px;
            margin-bottom: 16px;
        }
        p {
            font-size: 16px;
            line-height: 1.5;
            color: #444;
            margin: 12px 0;
        }
        .btn {
            display: block;
            width: 80%;
            max-width: 280px;
            margin: 20px auto;
            padding: 12px;
            text-align: center;
            background: #0039A6;
            color: #fff !important;
            font-size: 16px;
            font-weight: bold;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #0039A6;
        }
        .signature {
            text-align: center;
            color: #0039A6;
            font-weight: bold;
            font-size: 18px;
        }
        .footer {
            text-align: center;
            font-size: 14px;
            color: #666;
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    ${msg("custom.htmlEmailVerificationBody",user.firstName, link, linkExpiration)?no_esc}
</body>
</html>