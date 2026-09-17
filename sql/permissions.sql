-- REVIEW TEMPLATE ONLY: this script PRINTS commands; it creates no users or roles.
-- A database administrator must review and execute the printed commands separately.
-- Replace this with an existing least-privileged Entra database user.
-- NEVER use a dbo/db_owner/server admin identity for the interactive runtime.
-- db_datareader grants too broadly; use only SELECT on this workshop table.
-- Object DENY does not constrain dbo/sysadmin/owners. Review inherited roles too.
DECLARE @ExistingUser SYSNAME = N'REPLACE_WITH_EXISTING_ENTRA_DB_USER';
IF @ExistingUser = N'REPLACE_WITH_EXISTING_ENTRA_DB_USER'
    THROW 50001, 'Set @ExistingUser to an existing Entra database principal first.', 1;
IF DATABASE_PRINCIPAL_ID(@ExistingUser) IS NULL
    THROW 50002, 'Principal does not exist; provision/review it separately.', 1;
DECLARE @Quoted NVARCHAR(258) = QUOTENAME(@ExistingUser);
PRINT N'GRANT SELECT ON OBJECT::workshop.Record TO ' + @Quoted + N';';
PRINT N'DENY INSERT, UPDATE, DELETE, ALTER, CONTROL ON OBJECT::workshop.Record TO ' + @Quoted + N';';
-- This table holds all five synthetic scenarios. Python scopes queries but is NOT
-- a DB row-security boundary. Separate DBs/principals are needed for data isolation.
-- check --db reports effective write/admin permissions and rejects writable logins.
