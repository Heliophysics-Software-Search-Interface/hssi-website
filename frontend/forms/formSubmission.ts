
/** data that represents all fields in the software submission form */
export type SubmissionFormData = {
    submitterName?: string,
    persistentIdentifier?: string,
    codeRepositoryURL?: string,
    authors?: {
        authors?: string,
        authorIdentifier?: string,
        authorAffiliation?: {
            authorAffiliation?: string,
            authorAffiliationIdentifier?: string,
        }[],
    }[],
    softwareName?: string,
    description?: string,
    conciseDescription?: string,
    publicationDate?: string,
    publisher?: {
        publisher?: string,
        publisherIdentifier?: string,
    },
    versionNumber?: {
        versionNumber?: string,
        versionDate?: string,
        versionDescription?: string,
        versionPID?: string,
    },
    programmingLanguage?: string,
    license?: string,
    keywords?: string[],
    softwareFunctionality?: string[],
    dataSources?: string[],
    inputFormats?: string[],
    outputFormats?: string[],
    operatingSystem?: string[],
    cpuArchitecture?: string[],
    relatedRegion?: string[],
    referencePublication?: string,
    developmentStatus?: string,
    documentation?: string,
    funder?: {
        funder?: string,
        funderIdentifier?: string,
    }[],
    awardTitle?: {
        awardTitle?: string,
        awardNumber?: string,
    }[],
    relatedPublications?: string[],
    relatedDatasets?: string[],
    relatedSoftware?: string[],
    interoperableSoftware?: string[],
    relatedInstruments?: {
        relatedInstruments?: string,
        relatedInstrumentIdentifier?: string,
    }[],
    relatedObservatories?: {
        relatedObservatories?: string,
        relatedInstrumentIdentifier?: string,
    }[],
    logo?: string,
}

export class FormSubmission {

}