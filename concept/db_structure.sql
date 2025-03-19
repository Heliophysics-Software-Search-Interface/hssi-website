CREATE TABLE IF NOT EXISTS "OrganizationType" (
	"id" serial NOT NULL UNIQUE,
	"name" bigint NOT NULL UNIQUE,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Organizations" (
	"id" serial NOT NULL UNIQUE,
	"type" bigint NOT NULL,
	"name" varchar(255) NOT NULL,
	"abbreviation" varchar(255) NOT NULL,
	"parentOrganization" bigint NOT NULL,
	"website" varchar(255) NOT NULL,
	"identifier" varchar(255) NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Persons" (
	"id" serial NOT NULL UNIQUE,
	"name" varchar(255) NOT NULL,
	"lastName" varchar(255),
	"identifier" varchar(255),
	"affiliation" bigint NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "IvoaEntries" (
	"id" serial NOT NULL UNIQUE,
	"type" bigint NOT NULL,
	"name" varchar(255) NOT NULL,
	"identifier" varchar(255) NOT NULL,
	"ivoaEntry" varchar(255) NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "IvoaEntryType" (
	"id" serial NOT NULL UNIQUE,
	"name" varchar(255) NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "FunctionCategories" (
	"id" serial NOT NULL UNIQUE,
	"name" varchar(255) NOT NULL,
	"abbreviation" varchar(255) NOT NULL,
	"backgroundColor" double precision NOT NULL,
	"textColor" double precision NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Functionalities" (
	"id" serial NOT NULL UNIQUE,
	"name" varchar(255) NOT NULL,
	"abbbreviation" varchar(255) NOT NULL,
	"category" bigint NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "FileFormats" (
	"id" serial NOT NULL UNIQUE,
	"fullName" varchar(255) NOT NULL,
	"extension" varchar(255) NOT NULL,
	"affiliation" bigint NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Licenses" (
	"id" serial NOT NULL UNIQUE,
	"name" varchar(255) NOT NULL,
	"identifier" varchar(255) NOT NULL,
	"fullText" varchar(255) NOT NULL,
	"scheme" varchar(255) NOT NULL,
	"schemeUri" varchar(255) NOT NULL,
	"uri" varchar(255) NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Keywords" (
	"id" serial NOT NULL UNIQUE,
	"word" varchar(255) NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Awards" (
	"id" serial NOT NULL UNIQUE,
	"title" varchar(255) NOT NULL,
	"identifier" varchar(255) NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Images" (
	"id" serial NOT NULL UNIQUE,
	"uri" varchar(255) NOT NULL,
	"description" varchar(255) NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Phenomenas" (
	"id" serial NOT NULL UNIQUE,
	"name" varchar(255) NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Softwares" (
	"id" serial NOT NULL UNIQUE,
	"programmingLanguage" bigint NOT NULL,
	"publicationDate" timestamp with time zone NOT NULL,
	"authors" bigint NOT NULL,
	"publisher" bigint NOT NULL,
	"relatedInstruments" bigint NOT NULL,
	"relatedObservatories" bigint NOT NULL,
	"softwareName" varchar(255) NOT NULL,
	"versionNumber" varchar(255) NOT NULL,
	"versionDate" timestamp with time zone NOT NULL,
	"versionDescription" varchar(255) NOT NULL,
	"versionPid" varchar(255) NOT NULL,
	"PersistentIdentifier" varchar(255) NOT NULL,
	"referencePublication" varchar(255) NOT NULL,
	"description" varchar(255) NOT NULL,
	"conciseDescription" varchar(255) NOT NULL,
	"softwareFunctionality" bigint NOT NULL,
	"documentation" varchar(255) NOT NULL,
	"dataInputs" bigint NOT NULL,
	"supportedFileFormats" bigint NOT NULL,
	"relatedPublications" varchar(255) NOT NULL,
	"relatedDatasets" varchar(255) NOT NULL,
	"developmentStatus" bigint NOT NULL,
	"operatingSystem" bigint NOT NULL,
	"metadataLicense" bigint NOT NULL,
	"license" bigint NOT NULL,
	"relatedRegion" varchar(255) NOT NULL,
	"keywords" bigint NOT NULL,
	"relatedSoftware" varchar(255) NOT NULL,
	"interopableSoftware" varchar(255) NOT NULL,
	"funder" bigint NOT NULL,
	"award" bigint NOT NULL,
	"codeRepositoryUrl" varchar(255) NOT NULL,
	"logo" bigint NOT NULL,
	"relatedPhenomena" bigint NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "RepoStatuses" (
	"id" serial NOT NULL UNIQUE,
	"name" varchar(255) NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "OperatingSystems" (
	"id" serial NOT NULL UNIQUE,
	"name" varchar(255) NOT NULL,
	PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "ProgrammingLanguages" (
	"id" serial NOT NULL UNIQUE,
	"name" varchar(255) NOT NULL,
	"version" varchar(255) NOT NULL,
	"organization" bigint NOT NULL,
	PRIMARY KEY ("id")
);


ALTER TABLE "Organizations" ADD CONSTRAINT "Organizations_fk1" FOREIGN KEY ("type") REFERENCES "OrganizationType"("id");

ALTER TABLE "Organizations" ADD CONSTRAINT "Organizations_fk4" FOREIGN KEY ("parentOrganization") REFERENCES "Organizations"("id");
ALTER TABLE "Persons" ADD CONSTRAINT "Persons_fk4" FOREIGN KEY ("affiliation") REFERENCES "Organizations"("id");
ALTER TABLE "IvoaEntries" ADD CONSTRAINT "IvoaEntries_fk1" FOREIGN KEY ("type") REFERENCES "IvoaEntryType"("id");


ALTER TABLE "Functionalities" ADD CONSTRAINT "Functionalities_fk3" FOREIGN KEY ("category") REFERENCES "FunctionCategories"("id");
ALTER TABLE "FileFormats" ADD CONSTRAINT "FileFormats_fk3" FOREIGN KEY ("affiliation") REFERENCES "Organizations"("id");





ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk1" FOREIGN KEY ("programmingLanguage") REFERENCES "ProgrammingLanguages"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk3" FOREIGN KEY ("authors") REFERENCES "Persons"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk4" FOREIGN KEY ("publisher") REFERENCES "Organizations"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk5" FOREIGN KEY ("relatedInstruments") REFERENCES "IvoaEntries"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk6" FOREIGN KEY ("relatedObservatories") REFERENCES "IvoaEntries"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk16" FOREIGN KEY ("softwareFunctionality") REFERENCES "Functionalities"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk18" FOREIGN KEY ("dataInputs") REFERENCES "Functionalities"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk19" FOREIGN KEY ("supportedFileFormats") REFERENCES "FileFormats"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk22" FOREIGN KEY ("developmentStatus") REFERENCES "RepoStatuses"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk23" FOREIGN KEY ("operatingSystem") REFERENCES "OperatingSystems"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk24" FOREIGN KEY ("metadataLicense") REFERENCES "Licenses"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk25" FOREIGN KEY ("license") REFERENCES "Licenses"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk27" FOREIGN KEY ("keywords") REFERENCES "Keywords"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk30" FOREIGN KEY ("funder") REFERENCES "Organizations"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk31" FOREIGN KEY ("award") REFERENCES "Awards"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk33" FOREIGN KEY ("logo") REFERENCES "Images"("id");

ALTER TABLE "Softwares" ADD CONSTRAINT "Softwares_fk34" FOREIGN KEY ("relatedPhenomena") REFERENCES "Phenomenas"("id");


ALTER TABLE "ProgrammingLanguages" ADD CONSTRAINT "ProgrammingLanguages_fk3" FOREIGN KEY ("organization") REFERENCES "Organizations"("id");