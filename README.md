```.env
DISCORD_TOKEN=
CRAFTY_TOKEN=
WEBHOOK_URL=
SETUP_PASSWORD=
```

## Fix certificate error
`set PYTHONWARNINGS=ignore:Unverified HTTPS request`

### Permanent solution (windows)
    1. Open System Properties:
        - Press `Win + R`, type `sysdm.cpl`, and press Enter.
    2. Navigate to the **Advanced** tab and click **Environment Variables**.
    3. Under **System Variables** or **User Variables**, click **New**.
    4. Add the following:
        - **Variable Name**: `PYTHONWARNINGS`
        - **Variable Value**: `ignore:Unverified HTTPS request`
    5. Click **OK** to save.