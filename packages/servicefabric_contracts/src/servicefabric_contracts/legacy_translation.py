"""Conservative, deterministic and non-executing legacy translator."""
from __future__ import annotations
import hashlib, json
from pydantic import ValidationError
from .artifacts import StaticBundleArtifact
from .legacy_manifest import DuplicateJsonKey, LegacyManifest, parse_legacy_manifest, placeholders
from .service_package import ServicePackageDefinition
from .translation_context import TranslationContext
from .translation_diagnostics import diagnostic
from .translation_profiles import TEMPLATE_PROFILE, TranslationProfile
from .translation_report import LegacyManifestTranslationReport, TranslationSource

def _digest(source: bytes) -> str: return "sha256:" + hashlib.sha256(source).hexdigest()
def _canonical_digest(resource: ServicePackageDefinition) -> str:
    data=json.dumps(resource.model_dump(mode="json", by_alias=True), sort_keys=True, separators=(",",":"))
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()
def _substitute(value: str, context: TranslationContext) -> str:
    for name in ("APP_NAME", "APP_SLUG"):
        token="{{"+name+"}}"
        if token in value:
            if name not in context.parameters: raise KeyError(name)
            value=value.replace(token, context.parameters[name])
    return value
def _static_resource(manifest: LegacyManifest, context: TranslationContext) -> ServicePackageDefinition:
    if not isinstance(context.artifact, StaticBundleArtifact): raise ValueError("static profile requires immutable static artifact")
    name=_substitute(manifest.app_name, context)
    slug=_substitute(manifest.app_slug, context)
    if slug != context.package_id.split(".")[-1]: raise ValueError("legacy slug must match the context package identity component")
    owner=context.owner_ref.model_dump(mode="json")
    return ServicePackageDefinition.model_validate({
      "apiVersion":"servicefabric.ai/v1alpha1","kind":"ServicePackageDefinition",
      "metadata":{"id":context.package_id,"name":name,"namespace":context.namespace,"description":manifest.description,
        "labels":{"migration":"legacy"},"annotations":{"legacy-template":manifest.template},"owner_ref":owner},
      "spec":{"package_version":context.package_version,"description":manifest.description,"hosting":{"mode":"managed_static"},
        "artifact":context.artifact.model_dump(mode="json"),"entrypoints":[{"id":"web","kind":"web_ui","description":"Legacy frontend static entrypoint.","runtime_ref":"static:"+context.package_id,"machine_callable":False,"may_produce_effects":False,"exposures":[{"kind":"web"}]}],
        "declared_capabilities":[],"runtime_requirements":{},"network_policy":{"mode":"none"},"storage_requirements":[],"health":{"probe_kind":"none"},"ownership":{"owner_ref":owner},"lifecycle":{"maturity":"experimental","deprecation_status":"active","support_status":"best_effort"}}
    })

def translate_legacy_manifest(source: bytes, context: TranslationContext, source_reference: str = "manifest") -> LegacyManifestTranslationReport:
    base=dict(apiVersion="servicefabric.ai/v1alpha1", kind="LegacyManifestTranslationReport", source=TranslationSource(kind=context.source_kind, reference=source_reference), source_digest=_digest(source), profile=context.translation_profile)
    try: manifest=parse_legacy_manifest(source)
    except DuplicateJsonKey:
        return LegacyManifestTranslationReport(**base,status="invalid",diagnostics=(diagnostic("LEGACY_DUPLICATE_JSON_KEY","error","The manifest contains a duplicate JSON key.","","Remove duplicate keys."),),unmapped_fields=(),mapped_fields=(),discarded_fields=(),required_context=(),assumptions=())
    except (UnicodeError, json.JSONDecodeError, ValidationError, ValueError):
        return LegacyManifestTranslationReport(**base,status="invalid",diagnostics=(diagnostic("LEGACY_INVALID_JSON","error","The manifest is not a valid bounded legacy manifest.","","Correct the manifest structure without changing runtime semantics."),),unmapped_fields=(),mapped_fields=(),discarded_fields=(),required_context=(),assumptions=())
    diags=[diagnostic("LEGACY_RULES_ARE_ADVISORY_ONLY","warning","Legacy rules are advisory prose and were not converted into runtime authority.","/rules","Review during future canonical authoring."), diagnostic("LEGACY_TOOL_SEMANTICS_NOT_INFERRED","info","No tool lifecycle resources were inferred.","/rules","Author tools explicitly in later work.")]
    for key,value in sorted(manifest.core_services.items()):
        if value.startswith(("http://","ws://")): diags.append(diagnostic("LEGACY_INTERNAL_URL_NOT_PORTABLE","warning","An internal service URL was not copied into the canonical resource.",f"/core_services/{key}","Supply approved dependency references."))
        if value.startswith("/"): diags.append(diagnostic("LEGACY_HOST_PATH_NOT_PORTABLE","warning","A host path was not copied into the canonical resource.",f"/core_services/{key}","Replace it with an immutable artifact or dependency reference."))
    unknown=set(placeholders(manifest))-{"APP_NAME","APP_SLUG"}
    if unknown: diags.append(diagnostic("LEGACY_UNKNOWN_PLACEHOLDER","error","The manifest contains an unknown placeholder.","","Remove or explicitly migrate the unsupported placeholder."))
    missing=tuple(sorted(name for name in placeholders(manifest) if name not in context.parameters))
    if missing: diags.append(diagnostic("LEGACY_UNRESOLVED_PLACEHOLDER","error","Required placeholders remain unresolved.","","Supply validated APP_NAME and APP_SLUG parameters."))
    expected=TEMPLATE_PROFILE.get(manifest.template)
    if expected is None: diags.append(diagnostic("LEGACY_UNSUPPORTED_TEMPLATE","error","The template is not allowlisted for translation.","/template","Use assessment-only review or add a reviewed profile."))
    if context.translation_profile == TranslationProfile.LEGACY_FLASK_SHARED_HOST:
        diags.append(diagnostic("LEGACY_SHARED_HOST_REQUIRES_ADAPTER","error","The shared Flask blueprint host cannot be represented as an isolated artifact.","/template","Define a future shared-host adapter or migrate the package."))
    if context.translation_profile == TranslationProfile.LEGACY_COMPOSITE_UI_PYTHON:
        diags.append(diagnostic("COMPOSITE_PACKAGE_REQUIRES_SPLIT_REVIEW","error","UI and Python execution concerns require an explicit split review.","/template","Decide artifact ownership before canonical authoring."))
    resource=None
    if not any(d.severity=="error" for d in diags) and context.translation_profile == TranslationProfile.LEGACY_STATIC_FRONTEND:
        try: resource=_static_resource(manifest,context)
        except (KeyError,ValueError,ValidationError): diags.append(diagnostic("LEGACY_TRANSLATION_REQUIRES_REVIEW","error","Context does not support an honest static translation.","","Correct package identity and immutable artifact context."))
    status="translated_with_warnings" if resource else ("requires_split" if context.translation_profile == TranslationProfile.LEGACY_COMPOSITE_UI_PYTHON else "requires_context")
    if expected is None: status="unsupported"
    return LegacyManifestTranslationReport(**base,status=status,canonical_resource=resource,canonical_resource_digest=_canonical_digest(resource) if resource else None,diagnostics=tuple(sorted(diags,key=lambda d:(d.severity,d.code,d.source_pointer))),mapped_fields=("/app_name","/description","/template") if resource else (),unmapped_fields=("/core_services","/rules"),discarded_fields=(),required_context=missing,assumptions=(),requires_human_review=True)
