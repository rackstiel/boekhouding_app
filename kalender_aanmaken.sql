USE rick_lokaal;
GO

-- Verwijder de tabel als die al bestaat (handig bij opnieuw draaien)
IF OBJECT_ID('dbo.kalender', 'U') IS NOT NULL
    DROP TABLE dbo.kalender;
GO

SET LANGUAGE Dutch;

DECLARE @StartDate  date = '20251201';

-- 5 jaar in de toekomst
DECLARE @CutoffDate date = CAST(CONCAT(YEAR(GETDATE())+5,'1231') AS date);

;WITH seq(n) AS 
(
    SELECT 0 
    UNION ALL 
    SELECT n + 1 
    FROM seq
    WHERE n < DATEDIFF(DAY, @StartDate, @CutoffDate)
),
d(d) AS 
(
    SELECT DATEADD(DAY, n, @StartDate) 
    FROM seq
),
src AS
(
    SELECT
        TheDate         = CONVERT(date, d),
        TheDay          = DATEPART(DAY,       d),
        TheDayName      = DATENAME(WEEKDAY,   d),
        TheWeek         = DATEPART(WEEK,      d),
        TheISOWeek      = DATEPART(ISO_WEEK,  d),
        TheDayOfWeek    = DATEPART(WEEKDAY,   d),
        TheMonth        = DATEPART(MONTH,     d),
        TheMonthName    = DATENAME(MONTH,     d),
        TheQuarter      = DATEPART(Quarter,   d),
        TheYear         = DATEPART(YEAR,      d),
        TheFirstOfMonth = DATEFROMPARTS(YEAR(d), MONTH(d), 1),
        TheLastOfYear   = DATEFROMPARTS(YEAR(d), 12, 31),
        TheDayOfYear    = DATEPART(DAYOFYEAR, d)
    FROM d
),
dim AS
(
    SELECT
        ROW_NUMBER() OVER(ORDER BY TheDate ASC) DATUM_ID,
        TheDate DATUM, 
        FORMAT(TheDate, 'dd-MM-yyyy', 'nl-NL') DATUM_CHAR,
        TheDay DAG_NR,
        TheDayOfWeek WEEKDAG_NR,
        UPPER(LEFT(TheDayName,1))+LOWER(SUBSTRING(TheDayName,2,LEN(TheDayName))) WEEKDAG_NAAM,
        CONCAT(
            TheYear - CASE 
                WHEN TheMonth = 1  AND TheISOWeek > 51 THEN 1 
                WHEN TheMonth = 12 AND TheISOWeek = 1  THEN -1 
                ELSE 0 
            END,
            RIGHT('00'+CAST(TheISOWeek AS varchar),2)
        ) WEEK_ID,
        TheISOweek WEEK_NR,
        CONCAT('Week ',TheISOweek) WEEK_NAAM,
        UPPER(LEFT(FORMAT(TheDate, 'MMM'),1))+LOWER(SUBSTRING(FORMAT(TheDate, 'MMM'),2,LEN(FORMAT(TheDate, 'MMM')))) MAAND_KORT,
        CONCAT(TheYear,RIGHT('00'+CAST(TheMonth AS varchar),2)) MAAND_ID,
        TheMonth MAAND_NR,
        UPPER(LEFT(TheMonthName,1))+LOWER(SUBSTRING(TheMonthName,2,LEN(TheMonthName))) MAANDNAAM,
        CONCAT(TheYear,TheQuarter) KWARTAAL_ID,
        TheQuarter KWARTAAL_NR,
        CONCAT(TheQuarter,'e kwartaal') KWARTAALNAAM,
        TheYear JAAR_NR,
        CAST(TheYear AS varchar) JAAR_NAAM,
        TheYear - CASE 
            WHEN TheMonth = 1  AND TheISOWeek > 51 THEN 1 
            WHEN TheMonth = 12 AND TheISOWeek = 1  THEN -1 
            ELSE 0 
        END ISO_JAAR_NR,
        (TheYear*12)+TheMonth PERIODE_NR,
        ISWEEKEND = CASE 
            WHEN TheDayOfWeek IN (CASE @@DATEFIRST WHEN 1 THEN 6 WHEN 7 THEN 1 END,7) THEN 1 
            ELSE 0 
        END,
        EERSTE_DATUM_WEEK   = DATEADD(DAY, 1 - TheDayOfWeek, TheDate),
        LAATSTE_DATUM_WEEK  = DATEADD(DAY, 6, DATEADD(DAY, 1 - TheDayOfWeek, TheDate)),
        WEEKNR_IN_MAAND     = CONVERT(tinyint, DENSE_RANK() OVER (PARTITION BY TheYear, TheMonth ORDER BY TheWeek)),
        EERSTE_DATUM_MAAND  = MIN(TheDate) OVER (PARTITION BY TheYear, TheMonth),
        LAATSTE_DATUM_MAAND = MAX(TheDate) OVER (PARTITION BY TheYear, TheMonth),
        EERSTE_DATUM_VOLGENDE_MAAND = DATEADD(MONTH, 1, TheFirstOfMonth),
        LAATSTE_DATUM_VOLGENDE_MAAND = DATEADD(DAY, -1, DATEADD(MONTH, 2, TheFirstOfMonth)),
        EERSTE_DATUM_KWARTAAL  = MIN(TheDate) OVER (PARTITION BY TheYear, TheQuarter),
        LAATSTE_DATUM_KWARTAAL = MAX(TheDate) OVER (PARTITION BY TheYear, TheQuarter),
        IS_SCHRIKKELJAAR = CONVERT(bit, CASE 
            WHEN (TheYear % 400 = 0) OR (TheYear % 4 = 0 AND TheYear % 100 <> 0) THEN 1 
            ELSE 0 
        END),
        HEEFT_53_WEKEN = CASE 
            WHEN DATEPART(ISO_WEEK, TheLastOfYear) = 53 THEN 1 
            ELSE 0 
        END,
        JAAR_MAAND = CONVERT(char(4), TheYear) + RIGHT('00'+CAST(TheMonth AS varchar),2),
        [JAAR-MAAND] = CONCAT(TheYear,'-',RIGHT('00'+CAST(TheMonth AS varchar),2)),
        IS_VORIG_JAAR = CASE WHEN YEAR(GETDATE()) = TheYear+1 THEN 1 ELSE 0 END,
        IS_TOEKOMSTIG_JAAR = CASE WHEN YEAR(GETDATE()) < TheYear THEN 1 ELSE 0 END,
        IS_HUIDIG_JAAR = CASE WHEN YEAR(GETDATE()) = TheYear THEN 1 ELSE 0 END,
        IS_VORIGE_MAAND = CASE 
            WHEN ((YEAR(GETDATE())*12)+MONTH(GETDATE())) - ((TheYear*12)+TheMonth) = 1 THEN 1 
            ELSE 0 
        END,
        IS_TOEKOMSTIGE_MAAND = CASE 
            WHEN FORMAT(TheDate,'yyyyMM') > FORMAT(GETDATE(),'yyyyMM') THEN 1 
            ELSE 0 
        END,
        IS_HUIDIGE_MAAND = CASE 
            WHEN FORMAT(TheDate,'yyyyMM') = FORMAT(GETDATE(),'yyyyMM') THEN 1 
            ELSE 0 
        END,
        IS_TOEKOMSTIGE_DATUM = CASE WHEN TheDate > CAST(GETDATE() AS date) THEN 1 ELSE 0 END,
        IS_HUIDIGE_DATUM = CASE WHEN TheDate = CAST(GETDATE() AS date) THEN 1 ELSE 0 END,
        IS_VOORGAANDE_12_MAAND = CASE 
            WHEN ((YEAR(GETDATE())*12)+MONTH(GETDATE())) - ((TheYear*12)+TheMonth) BETWEEN 1 AND 12 THEN 1 
            ELSE 0 
        END
    FROM src
)

-- 👇 Hier gebeurt de magie: tabel wordt aangemaakt
SELECT 
    dim.*,
    'SQL' AS M_BRON,
    GETDATE() AS M_DATUM_TIJD_VERVERST
INTO dbo.kalender
FROM dim
ORDER BY DATUM
OPTION (MAXRECURSION 0);
GO