/*!
 * Lunr languages, `Kannada` language
 * https://github.com/MiKr13/lunr-languages
 *
 * Copyright 2023, India
 * http://www.mozilla.org/MPL/
 */
/*!
 * based on
 * Snowball JavaScript Library v0.3
 * http://code.google.com/p/urim/
 * http://snowball.tartarus.org/
 *
 * Copyright 2010, Oleg Mazko
 * http://www.mozilla.org/MPL/
 */

/**
 * export the module via AMD, CommonJS or as a browser global
 * Export code from https://github.com/umdjs/umd/blob/master/returnExports.js
 */
;
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD. Register as an anonymous module.
    define(factory)
  } else if (typeof exports === 'object') {
    /**
     * Node. Does not work with strict CommonJS, but
     * only CommonJS-like environments that support module.exports,
     * like Node.
     */
    module.exports = factory()
  } else {
    // Browser globals (root is window)
    factory()(root.lunr);
  }
}(this, function() {
  /**
   * Just return a value to define the module export.
   * This example returns an object, but the module
   * can return a function as the exported value.
   */
  return function(lunr) {
    /* throw error if lunr is not yet included */
    if ('undefined' === typeof lunr) {
      throw new Error('Lunr is not present. Please include / require Lunr before this script.');
    }

    /* throw error if lunr stemmer support is not yet included */
    if ('undefined' === typeof lunr.stemmerSupport) {
      throw new Error('Lunr stemmer support is not present. Please include / require Lunr stemmer support before this script.');
    }

    /* register specific locale function */
    lunr.kn = function() {
      this.pipeline.reset();
      this.pipeline.add(
        lunr.kn.trimmer,
        lunr.kn.stopWordFilter,
        lunr.kn.stemmer
      );

      if (this.searchPipeline) {
        this.searchPipeline.reset();
        this.searchPipeline.add(lunr.kn.stemmer)
      }
    };

    /* lunr trimmer function */
    lunr.kn.wordCharacters = "\u0C80-\u0C84\u0C85-\u0C94\u0C95-\u0CB9\u0CBE-\u0CCC\u0CBC-\u0CBD\u0CD5-\u0CD6\u0CDD-\u0CDE\u0CE0-\u0CE1\u0CE2-\u0CE3\u0CE4\u0CE5\u0CE6-\u0CEF\u0CF1-\u0CF3";
    lunr.kn.trimmer = lunr.trimmerSupport.generateTrimmer(lunr.kn.wordCharacters);

    lunr.Pipeline.registerFunction(lunr.kn.trimmer, 'trimmer-kn');
    /* lunr stop word filter */
    lunr.kn.stopWordFilter = lunr.generateStopWordFilter(
      'ಮತ್ತು ಈ ಒಂದು ರಲ್ಲಿ ಹಾಗೂ ಎಂದು ಅಥವಾ ಇದು ರ ಅವರು ಎಂಬ ಮೇಲೆ ಅವರ ತನ್ನ ಆದರೆ ತಮ್ಮ ನಂತರ ಮೂಲಕ ಹೆಚ್ಚು ನ ಆ ಕೆಲವು ಅನೇಕ ಎರಡು ಹಾಗು ಪ್ರಮುಖ ಇದನ್ನು ಇದರ ಸುಮಾರು ಅದರ ಅದು ಮೊದಲ ಬಗ್ಗೆ ನಲ್ಲಿ ರಂದು ಇತರ ಅತ್ಯಂತ ಹೆಚ್ಚಿನ ಸಹ ಸಾಮಾನ್ಯವಾಗಿ ನೇ ಹಲವಾರು ಹೊಸ ದಿ ಕಡಿಮೆ ಯಾವುದೇ ಹೊಂದಿದೆ ದೊಡ್ಡ ಅನ್ನು ಇವರು ಪ್ರಕಾರ ಇದೆ ಮಾತ್ರ ಕೂಡ ಇಲ್ಲಿ ಎಲ್ಲಾ ವಿವಿಧ ಅದನ್ನು ಹಲವು ರಿಂದ ಕೇವಲ ದ ದಕ್ಷಿಣ ಗೆ ಅವನ ಅತಿ ನೆಯ ಬಹಳ ಕೆಲಸ ಎಲ್ಲ ಪ್ರತಿ ಇತ್ಯಾದಿ ಇವು ಬೇರೆ ಹೀಗೆ ನಡುವೆ ಇದಕ್ಕೆ ಎಸ್ ಇವರ ಮೊದಲು ಶ್ರೀ ಮಾಡುವ ಇದರಲ್ಲಿ ರೀತಿಯ ಮಾಡಿದ ಕಾಲ ಅಲ್ಲಿ ಮಾಡಲು ಅದೇ ಈಗ ಅವು ಗಳು ಎ ಎಂಬುದು ಅವನು ಅಂದರೆ ಅವರಿಗೆ ಇರುವ ವಿಶೇಷ ಮುಂದೆ ಅವುಗಳ ಮುಂತಾದ ಮೂಲ ಬಿ ಮೀ ಒಂದೇ ಇನ್ನೂ ಹೆಚ್ಚಾಗಿ ಮಾಡಿ ಅವರನ್ನು ಇದೇ ಯ ರೀತಿಯಲ್ಲಿ ಜೊತೆ ಅದರಲ್ಲಿ ಮಾಡಿದರು ನಡೆದ ಆಗ ಮತ್ತೆ ಪೂರ್ವ ಆತ ಬಂದ ಯಾವ ಒಟ್ಟು ಇತರೆ ಹಿಂದೆ ಪ್ರಮಾಣದ ಗಳನ್ನು ಕುರಿತು ಯು ಆದ್ದರಿಂದ ಅಲ್ಲದೆ ನಗರದ ಮೇಲಿನ ಏಕೆಂದರೆ ರಷ್ಟು ಎಂಬುದನ್ನು ಬಾರಿ ಎಂದರೆ ಹಿಂದಿನ ಆದರೂ ಆದ ಸಂಬಂಧಿಸಿದ ಮತ್ತೊಂದು ಸಿ ಆತನ '.split(' '));
    /* lunr stemmer function */
    lunr.kn.stemmer = (function() {

      return function(word) {
        // for lunr version 2
        if (typeof word.update === "function") {
          return word.update(function(word) {
            return word;
          })
        } else { // for lunr version <= 1
          return word;
        }

      }
    })();

    var segmenter = lunr.wordcut;
    segmenter.init();
    lunr.kn.tokenizer = function(obj) {
      if (!arguments.length || obj == null || obj == undefined) return []
      if (Array.isArray(obj)) return obj.map(function(t) {
        return isLunr2 ? new lunr.Token(t.toLowerCase()) : t.toLowerCase()
      });

      var str = obj.toString().toLowerCase().replace(/^\s+/, '');
      return segmenter.cut(str).split('|');
    }

    lunr.Pipeline.registerFunction(lunr.kn.stemmer, 'stemmer-kn');
    lunr.Pipeline.registerFunction(lunr.kn.stopWordFilter, 'stopWordFilter-kn');

  };
}))