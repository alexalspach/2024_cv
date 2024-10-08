function loadContentAndScroll(tabId, anchorId) {
  var contentDivId;
  var contentUrl;
  switch (tabId) {
    case 'projects':
      contentDivId = '#includeProjects';
      contentUrl = 'projects.html';
      break;
    case 'work':
      contentDivId = '#includeExperience';
      contentUrl = 'experience.html';
      break;
    case 'education':
      contentDivId = '#includeEducation';
      contentUrl = 'education.html';
      break;
    case 'publications':
      contentDivId = '#includePapers';
      contentUrl = 'paperspatents.html';
      break;
    case 'me':
      contentDivId = '#includeMe';
      contentUrl = 'me.html';
      break;
    // Add other cases as needed
    default:
      return;
  }

  $(contentDivId).load(contentUrl, function () {
    if (anchorId) {
      var target = $('#' + anchorId);
      if (target.length) {
        $('html, body').animate(
          {
            scrollTop: target.offset().top,
          },
          1000
        );
      }
    }
  });
}