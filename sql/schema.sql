SET NOCOUNT ON;
SET XACT_ABORT ON;
IF SCHEMA_ID(N'workshop') IS NULL
    EXEC(N'CREATE SCHEMA workshop AUTHORIZATION dbo;');
IF OBJECT_ID(N'workshop.Record', N'U') IS NULL
BEGIN
    CREATE TABLE workshop.Record (
        scenario NVARCHAR(32) NOT NULL,
        record_id NVARCHAR(64) NOT NULL,
        category NVARCHAR(32) NOT NULL,
        payload NVARCHAR(MAX) NOT NULL,
        CONSTRAINT PK_WorkshopRecord PRIMARY KEY (scenario, record_id),
        CONSTRAINT CK_WorkshopRecordJson CHECK (ISJSON(payload) = 1)
    );
END;
