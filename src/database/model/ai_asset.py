from database.model.resource import Resource


class AIAssetOld(Resource):
    """
    Many resources, such as dataset and publication, are a type of AIAssetOld
    and should therefore inherit from this AIAssetOld class.
    Shared fields can be defined on this class.

    Notice the difference between AIAssetOld and AIAssetOldTable.
    The latter enables defining a relationship to "any AI Asset",
    by making sure that the identifiers of all resources that
    are AIAssetOlds, are unique over the AIAssetOlds.
    """
