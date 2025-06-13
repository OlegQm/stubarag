# Keycloak

## Instructions for Using Keycloak Authentication During Development

**You need to create an account to access both the chat app and the admin interface.**

Your account is stored in the associated volume of the `postgres` container. This account will remain permanent unless you delete the volume.

### How to Create an Account:

1.  Open the chat app on `localhost:80`.
2.  Click the `Log in` button.
3.  A popup window will appear. At the bottom of the login form, click on the `Register` option.
4.  Complete the `Register` form. Once successfully completed, you will be automatically redirected to the chat app.
5.  From this point onward, you can use your account to log in to both the chat app and the admin interface.

### Accessing the Keycloak Admin Interface

To access the Keycloak server admin interface on `localhost:8088/admin/`, use the following credentials:

-   **Username:** admin
-   **Password:** admin

**Please note:** All changes made to the Keycloak configuration are temporary and will remain until the Keycloak container is deleted.

If you have any questions, feel free to contact @BHnila.
